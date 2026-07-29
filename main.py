# -*- coding: utf-8 -*-
"""
섭외 메세지 생성기
- 템플릿 안의 [ ] 항목만 채우면 메세지가 자동 완성됩니다.
- 템플릿은 프로그램 안에서 자유롭게 추가/수정/삭제할 수 있습니다.
- templates.json 파일에 템플릿이 저장되며, 이 파일이 없으면 기본 템플릿 3종으로 새로 만듭니다.
"""

import json
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# ------------------------------------------------------------------
# 경로 설정 (exe로 빌드했을 때도 exe 파일 옆에 templates.json이 생기도록 처리)
# ------------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_PATH = os.path.join(BASE_DIR, "templates.json")

PLACEHOLDER_PATTERN = re.compile(r"\[([^\[\]]+)\]")

# ------------------------------------------------------------------
# 컬러 / 폰트 팔레트
# ------------------------------------------------------------------
BG = "#F2F4F8"          # 전체 배경
CARD = "#FFFFFF"        # 카드 배경
BORDER = "#E4E7EC"      # 카드 테두리
TEXT_MAIN = "#1B1F27"
TEXT_SUB = "#6B7280"
PRIMARY = "#00B894"     # 포인트 컬러 (민트/그린)
PRIMARY_DARK = "#00A383"
HEADER_BG = "#101820"

FONT_BASE = ("맑은 고딕", 10)
FONT_SECTION = ("맑은 고딕", 11, "bold")
FONT_LABEL = ("맑은 고딕", 9, "bold")
FONT_HEADER = ("맑은 고딕", 13, "bold")
FONT_BTN = ("맑은 고딕", 10, "bold")

DEFAULT_TEMPLATES = [
    {
        "name": "① 지원 확인 + 가이드 전달",
        "body": (
            "안녕하세요! :)\n\n"
            "[모집공고 제목] 셀프캠 영상에 지원해주신 메일보고 연락드렸습니다! :)\n\n"
            "우선 지원해주셔서 감사합니다! :)\n\n"
            "진행 전에 가이드도 전달드리겠습니다!\n"
            "확인해주시고, 진행여부 연락 주시면 이후 진행하겠습니다! :)\n\n"
            "가이드 링크 : [가이드 링크]"
        ),
    },
    {
        "name": "② 입금자명 / 입금일 안내",
        "body": (
            "안녕하세요! :)\n\n"
            "[모집공고 제목] 건 입금 관련하여 안내드립니다!\n\n"
            "입금자명 : [입금자명]\n"
            "입금 예정일 : [입금 예정일]\n\n"
            "확인 부탁드리며, 궁금하신 점 있으시면 언제든 편하게 연락 주세요! :)"
        ),
    },
    {
        "name": "③ 진행 거절 안내",
        "body": (
            "안녕하세요! :)\n\n"
            "[모집공고 제목] 건으로 연락드립니다.\n\n"
            "내부적으로 논의한 결과, 이번 건은 아쉽게도 [거절 사유]로 인해 "
            "함께 진행이 어려울 것 같아 안내드립니다ㅠㅠ\n\n"
            "관심 가져주시고 지원해주셔서 정말 감사드리며,\n"
            "다음에 좋은 기회로 또 함께할 수 있으면 좋겠습니다! :)"
        ),
    },
]


def load_templates():
    if not os.path.exists(TEMPLATES_PATH):
        save_templates(DEFAULT_TEMPLATES)
        return [dict(t) for t in DEFAULT_TEMPLATES]
    try:
        with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return [dict(t) for t in DEFAULT_TEMPLATES]


def save_templates(templates):
    with open(TEMPLATES_PATH, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


def extract_placeholders(text):
    """텍스트에 등장하는 순서대로, 중복 없이 [ ] 안의 항목 이름을 반환"""
    seen = []
    for m in PLACEHOLDER_PATTERN.finditer(text):
        name = m.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def card(parent, **kwargs):
    """흰 배경 + 옅은 테두리를 가진 '카드'처럼 보이는 프레임"""
    outer = tk.Frame(parent, bg=BORDER, **kwargs)
    inner = tk.Frame(outer, bg=CARD)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


# ------------------------------------------------------------------
# 템플릿 추가/수정 다이얼로그
# ------------------------------------------------------------------
class TemplateEditDialog(tk.Toplevel):
    def __init__(self, parent, name="", body=""):
        super().__init__(parent)
        self.title("템플릿 편집")
        self.geometry("580x520")
        self.configure(bg=BG)
        self.result = None
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 20, "pady": (16, 4)}

        tk.Label(self, text="템플릿 이름", font=FONT_LABEL, bg=BG, fg=TEXT_MAIN).pack(
            anchor="w", **pad
        )
        self.name_entry = tk.Entry(
            self, font=FONT_BASE, relief="flat", bg="#FFFFFF",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY,
        )
        self.name_entry.pack(fill="x", padx=20, ipady=6)
        self.name_entry.insert(0, name)

        tk.Label(
            self,
            text="본문  (바뀌는 부분은 대괄호로 감싸주세요. 예: [모집공고 제목])",
            font=FONT_LABEL, bg=BG, fg=TEXT_MAIN,
        ).pack(anchor="w", **pad)

        body_outer, body_inner = card(self)
        body_outer.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.body_text = tk.Text(
            body_inner, font=FONT_BASE, wrap="word", relief="flat",
            bg=CARD, fg=TEXT_MAIN, padx=10, pady=10,
        )
        scroll = tk.Scrollbar(body_inner, command=self.body_text.yview)
        self.body_text.configure(yscrollcommand=scroll.set)
        self.body_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.body_text.insert("1.0", body)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=16)
        tk.Button(
            btn_frame, text="취소", width=10, font=FONT_BASE, relief="flat",
            bg="#E5E7EB", fg=TEXT_MAIN, activebackground="#D1D5DB",
            command=self.destroy,
        ).pack(side="right", padx=(6, 0), ipady=4)
        tk.Button(
            btn_frame, text="저장", width=10, font=FONT_BTN, relief="flat",
            bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
            command=self._on_save,
        ).pack(side="right", ipady=4)

    def _on_save(self):
        name = self.name_entry.get().strip()
        body = self.body_text.get("1.0", "end-1c")
        if not name:
            messagebox.showwarning("확인", "템플릿 이름을 입력해주세요.")
            return
        if not body.strip():
            messagebox.showwarning("확인", "본문을 입력해주세요.")
            return
        self.result = {"name": name, "body": body}
        self.destroy()


# ------------------------------------------------------------------
# 메인 애플리케이션
# ------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("섭외 메세지 생성기")
        self.geometry("1080x680")
        self.minsize(920, 580)
        self.configure(bg=BG)

        self.templates = load_templates()
        self.selected_index = None
        self.field_vars = {}      # placeholder name -> tk.StringVar
        self.field_entries = {}   # placeholder name -> tk.Entry

        self._build_style()
        self._build_header()
        self._build_layout()
        self._refresh_template_list()

    # ---------------- 스타일 ----------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TScrollbar", background=BORDER, troughcolor=BG, borderwidth=0)

    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, height=54)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(
            header, text="✉  섭외 메세지 생성기", font=FONT_HEADER,
            bg=HEADER_BG, fg="white",
        ).pack(side="left", padx=20)

    # ---------------- UI 구성 ----------------
    def _build_layout(self):
        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(fill="both", expand=True)

        # 왼쪽: 템플릿 목록
        left_outer, left = card(root_frame, width=270)
        left_outer.pack(side="left", fill="y", padx=(16, 8), pady=16)
        left_outer.pack_propagate(False)

        tk.Label(
            left, text="템플릿 목록", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        list_frame = tk.Frame(left, bg=CARD)
        list_frame.pack(fill="both", expand=True, padx=16)
        self.template_listbox = tk.Listbox(
            list_frame, font=FONT_BASE, activestyle="none", relief="flat",
            bg=CARD, fg=TEXT_MAIN, highlightthickness=0,
            selectbackground=PRIMARY, selectforeground="white",
            bd=0,
        )
        list_scroll = tk.Scrollbar(list_frame, command=self.template_listbox.yview)
        self.template_listbox.configure(yscrollcommand=list_scroll.set)
        self.template_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.template_listbox.bind("<<ListboxSelect>>", self._on_select_template)

        btns = tk.Frame(left, bg=CARD)
        btns.pack(fill="x", padx=16, pady=14)
        self._small_btn(btns, "＋ 추가", self._add_template, PRIMARY, "white").pack(
            side="left", expand=True, fill="x", padx=(0, 4)
        )
        self._small_btn(btns, "수정", self._edit_template, "#E5E7EB", TEXT_MAIN).pack(
            side="left", expand=True, fill="x", padx=4
        )
        self._small_btn(btns, "삭제", self._delete_template, "#FEE2E2", "#B91C1C").pack(
            side="left", expand=True, fill="x", padx=(4, 0)
        )

        # 가운데: 항목 입력
        mid_outer, mid = card(root_frame, width=310)
        mid_outer.pack(side="left", fill="both", padx=8, pady=16)
        mid_outer.pack_propagate(False)

        tk.Label(
            mid, text="변경할 항목 입력", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        canvas = tk.Canvas(mid, highlightthickness=0, bg=CARD)
        vscroll = tk.Scrollbar(mid, orient="vertical", command=canvas.yview)
        self.fields_frame = tk.Frame(canvas, bg=CARD)
        self.fields_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.fields_frame, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0))
        vscroll.pack(side="right", fill="y", padx=(0, 4))
        self.fields_canvas = canvas

        self._primary_btn(mid, "메세지 생성 ▶", self._generate_message).pack(
            fill="x", padx=16, pady=14, ipady=6
        )

        # 오른쪽: 미리보기
        right_outer, right = card(root_frame)
        right_outer.pack(side="left", fill="both", expand=True, padx=(8, 16), pady=16)

        tk.Label(
            right, text="미리보기", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        preview_frame = tk.Frame(right, bg=CARD)
        preview_frame.pack(fill="both", expand=True, padx=16)
        self.preview_text = tk.Text(
            preview_frame, font=("맑은 고딕", 11), wrap="word", state="disabled",
            relief="flat", bg="#F8F9FB", fg=TEXT_MAIN, padx=14, pady=14,
            highlightthickness=1, highlightbackground=BORDER,
        )
        preview_scroll = tk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        self._accent_btn(right, "📋  클립보드로 복사", self._copy_to_clipboard).pack(
            fill="x", padx=16, pady=(12, 4), ipady=7
        )

        self.status_label = tk.Label(
            right, text="", fg=TEXT_SUB, bg=CARD, font=("맑은 고딕", 9)
        )
        self.status_label.pack(anchor="w", padx=16, pady=(0, 14))

    # ---------------- 버튼 헬퍼 ----------------
    def _small_btn(self, parent, text, command, bg, fg):
        return tk.Button(
            parent, text=text, command=command, font=("맑은 고딕", 9, "bold"),
            relief="flat", bg=bg, fg=fg, activebackground=bg, bd=0,
            cursor="hand2", pady=6,
        )

    def _primary_btn(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, font=FONT_BTN,
            relief="flat", bg=PRIMARY_DARK, fg="white",
            activebackground=PRIMARY, activeforeground="white",
            bd=0, cursor="hand2",
        )

    def _accent_btn(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, font=FONT_BTN,
            relief="flat", bg=PRIMARY, fg="white",
            activebackground=PRIMARY_DARK, activeforeground="white",
            bd=0, cursor="hand2",
        )

    # ---------------- 템플릿 목록 로직 ----------------
    def _refresh_template_list(self, keep_selection=True):
        prev = self.selected_index
        self.template_listbox.delete(0, "end")
        for t in self.templates:
            self.template_listbox.insert("end", "  " + t["name"])
        save_templates(self.templates)
        if keep_selection and prev is not None and prev < len(self.templates):
            self.template_listbox.selection_set(prev)
            self._load_fields_for(prev)
        else:
            self._clear_fields()

    def _on_select_template(self, event):
        sel = self.template_listbox.curselection()
        if not sel:
            return
        self._load_fields_for(sel[0])

    def _load_fields_for(self, index):
        self.selected_index = index
        template = self.templates[index]
        placeholders = extract_placeholders(template["body"])

        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.field_vars = {}
        self.field_entries = {}

        if not placeholders:
            tk.Label(
                self.fields_frame,
                text="이 템플릿에는 변경할 [ ] 항목이 없습니다.",
                fg=TEXT_SUB, bg=CARD, wraplength=260, justify="left",
            ).pack(anchor="w", pady=8, padx=4)
        else:
            for name in placeholders:
                tk.Label(
                    self.fields_frame, text=name, font=FONT_LABEL,
                    bg=CARD, fg=TEXT_MAIN,
                ).pack(anchor="w", padx=4, pady=(10, 3))

                var = tk.StringVar()
                # StringVar의 write 트레이스를 사용해야 한글(IME) 조합 중에도
                # 글자가 깨지지 않고 정확한 시점에만 미리보기가 갱신됩니다.
                var.trace_add(
                    "write", lambda *args: self._update_preview_from_fields(auto=True)
                )
                entry = tk.Entry(
                    self.fields_frame, font=FONT_BASE, textvariable=var,
                    relief="flat", bg="#F8F9FB", fg=TEXT_MAIN,
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=PRIMARY, insertbackground=TEXT_MAIN,
                )
                entry.pack(anchor="w", padx=4, fill="x", ipady=5)
                self.field_vars[name] = var
                self.field_entries[name] = entry

        self._update_preview_from_fields(auto=True)

    def _clear_fields(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.field_vars = {}
        self.field_entries = {}
        self.selected_index = None
        self._set_preview("")

    # ---------------- 템플릿 추가/수정/삭제 ----------------
    def _add_template(self):
        dlg = TemplateEditDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.templates.append(dlg.result)
            self._refresh_template_list(keep_selection=False)
            self.template_listbox.selection_set(len(self.templates) - 1)
            self._load_fields_for(len(self.templates) - 1)

    def _edit_template(self):
        sel = self.template_listbox.curselection()
        if not sel:
            messagebox.showinfo("확인", "수정할 템플릿을 먼저 선택해주세요.")
            return
        idx = sel[0]
        t = self.templates[idx]
        dlg = TemplateEditDialog(self, name=t["name"], body=t["body"])
        self.wait_window(dlg)
        if dlg.result:
            self.templates[idx] = dlg.result
            self._refresh_template_list()
            self.template_listbox.selection_set(idx)
            self._load_fields_for(idx)

    def _delete_template(self):
        sel = self.template_listbox.curselection()
        if not sel:
            messagebox.showinfo("확인", "삭제할 템플릿을 먼저 선택해주세요.")
            return
        idx = sel[0]
        if messagebox.askyesno(
            "삭제 확인", f"'{self.templates[idx]['name']}' 템플릿을 삭제할까요?"
        ):
            del self.templates[idx]
            self.selected_index = None
            self._refresh_template_list(keep_selection=False)

    # ---------------- 메세지 생성 ----------------
    def _update_preview_from_fields(self, auto=False):
        if self.selected_index is None:
            return
        template = self.templates[self.selected_index]
        text = template["body"]

        def repl(m):
            key = m.group(1)
            var = self.field_vars.get(key)
            val = var.get().strip() if var else ""
            return val if val else f"[{key}]"

        result = PLACEHOLDER_PATTERN.sub(repl, text)
        self._set_preview(result)
        if auto:
            self.status_label.config(text="")

    def _generate_message(self):
        if self.selected_index is None:
            messagebox.showinfo("확인", "먼저 왼쪽에서 템플릿을 선택해주세요.")
            return
        self._update_preview_from_fields()
        self.status_label.config(text="메세지가 생성되었습니다. 아래 복사 버튼을 눌러주세요.")

    def _set_preview(self, text):
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def _copy_to_clipboard(self):
        text = self.preview_text.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showinfo("확인", "복사할 내용이 없습니다. 먼저 메세지를 생성해주세요.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_label.config(text="✅ 클립보드에 복사되었습니다!")


if __name__ == "__main__":
    app = App()
    app.mainloop()
