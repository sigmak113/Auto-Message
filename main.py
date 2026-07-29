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
from tkinter import ttk, messagebox, simpledialog

# ------------------------------------------------------------------
# 경로 설정 (exe로 빌드했을 때도 exe 파일 옆에 templates.json이 생기도록 처리)
# ------------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_PATH = os.path.join(BASE_DIR, "templates.json")

PLACEHOLDER_PATTERN = re.compile(r"\[([^\[\]]+)\]")

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


# ------------------------------------------------------------------
# 템플릿 추가/수정 다이얼로그
# ------------------------------------------------------------------
class TemplateEditDialog(tk.Toplevel):
    def __init__(self, parent, name="", body=""):
        super().__init__(parent)
        self.title("템플릿 편집")
        self.geometry("560x480")
        self.result = None
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 12, "pady": 6}

        tk.Label(self, text="템플릿 이름", font=("맑은 고딕", 10, "bold")).pack(
            anchor="w", **pad
        )
        self.name_entry = tk.Entry(self, font=("맑은 고딕", 10))
        self.name_entry.pack(fill="x", padx=12)
        self.name_entry.insert(0, name)

        tk.Label(
            self,
            text="본문  (바뀌는 부분은 대괄호로 감싸주세요. 예: [모집공고 제목])",
            font=("맑은 고딕", 10, "bold"),
        ).pack(anchor="w", **pad)

        body_frame = tk.Frame(self)
        body_frame.pack(fill="both", expand=True, padx=12)
        self.body_text = tk.Text(body_frame, font=("맑은 고딕", 10), wrap="word")
        scroll = tk.Scrollbar(body_frame, command=self.body_text.yview)
        self.body_text.configure(yscrollcommand=scroll.set)
        self.body_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.body_text.insert("1.0", body)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=12, pady=12)
        tk.Button(btn_frame, text="저장", width=10, command=self._on_save).pack(
            side="right", padx=4
        )
        tk.Button(btn_frame, text="취소", width=10, command=self.destroy).pack(
            side="right", padx=4
        )

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
        self.geometry("1000x640")
        self.minsize(860, 560)

        self.templates = load_templates()
        self.selected_index = None
        self.field_entries = {}  # placeholder name -> tk.Entry

        self._build_layout()
        self._refresh_template_list()

    # ---------------- UI 구성 ----------------
    def _build_layout(self):
        root_frame = tk.Frame(self)
        root_frame.pack(fill="both", expand=True)

        # 왼쪽: 템플릿 목록
        left = tk.Frame(root_frame, width=260)
        left.pack(side="left", fill="y", padx=(10, 4), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="템플릿 목록", font=("맑은 고딕", 11, "bold")).pack(
            anchor="w"
        )

        list_frame = tk.Frame(left)
        list_frame.pack(fill="both", expand=True, pady=6)
        self.template_listbox = tk.Listbox(
            list_frame, font=("맑은 고딕", 10), activestyle="none"
        )
        list_scroll = tk.Scrollbar(list_frame, command=self.template_listbox.yview)
        self.template_listbox.configure(yscrollcommand=list_scroll.set)
        self.template_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.template_listbox.bind("<<ListboxSelect>>", self._on_select_template)

        btns = tk.Frame(left)
        btns.pack(fill="x", pady=4)
        tk.Button(btns, text="추가", command=self._add_template).pack(
            side="left", expand=True, fill="x", padx=2
        )
        tk.Button(btns, text="수정", command=self._edit_template).pack(
            side="left", expand=True, fill="x", padx=2
        )
        tk.Button(btns, text="삭제", command=self._delete_template).pack(
            side="left", expand=True, fill="x", padx=2
        )

        # 가운데: 항목 입력
        mid = tk.Frame(root_frame, width=320)
        mid.pack(side="left", fill="both", padx=4, pady=10)
        mid.pack_propagate(False)

        tk.Label(mid, text="변경할 항목 입력", font=("맑은 고딕", 11, "bold")).pack(
            anchor="w"
        )

        canvas = tk.Canvas(mid, highlightthickness=0)
        vscroll = tk.Scrollbar(mid, orient="vertical", command=canvas.yview)
        self.fields_frame = tk.Frame(canvas)
        self.fields_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.fields_frame, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True, pady=6)
        vscroll.pack(side="right", fill="y")
        self.fields_canvas = canvas

        tk.Button(
            mid, text="메세지 생성 ▶", font=("맑은 고딕", 10, "bold"),
            command=self._generate_message, bg="#3B82F6", fg="white"
        ).pack(fill="x", pady=8)

        # 오른쪽: 미리보기
        right = tk.Frame(root_frame)
        right.pack(side="left", fill="both", expand=True, padx=(4, 10), pady=10)

        tk.Label(right, text="미리보기", font=("맑은 고딕", 11, "bold")).pack(anchor="w")

        preview_frame = tk.Frame(right)
        preview_frame.pack(fill="both", expand=True, pady=6)
        self.preview_text = tk.Text(
            preview_frame, font=("맑은 고딕", 11), wrap="word", state="disabled"
        )
        preview_scroll = tk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        tk.Button(
            right, text="📋 클립보드로 복사", font=("맑은 고딕", 10, "bold"),
            command=self._copy_to_clipboard, bg="#10B981", fg="white"
        ).pack(fill="x", pady=4)

        self.status_label = tk.Label(right, text="", fg="#555")
        self.status_label.pack(anchor="w", pady=(4, 0))

    # ---------------- 템플릿 목록 로직 ----------------
    def _refresh_template_list(self, keep_selection=True):
        prev = self.selected_index
        self.template_listbox.delete(0, "end")
        for t in self.templates:
            self.template_listbox.insert("end", t["name"])
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
        self.field_entries = {}

        if not placeholders:
            tk.Label(
                self.fields_frame,
                text="이 템플릿에는 변경할 [ ] 항목이 없습니다.",
                fg="#777",
                wraplength=280,
                justify="left",
            ).pack(anchor="w", pady=8, padx=4)
        else:
            for name in placeholders:
                tk.Label(
                    self.fields_frame, text=name, font=("맑은 고딕", 9, "bold")
                ).pack(anchor="w", padx=4, pady=(8, 0))
                entry = tk.Entry(self.fields_frame, font=("맑은 고딕", 10), width=32)
                entry.pack(anchor="w", padx=4, fill="x")
                self.field_entries[name] = entry

        self._update_preview_from_fields(auto=True)

    def _clear_fields(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
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
            entry = self.field_entries.get(key)
            val = entry.get().strip() if entry else ""
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
