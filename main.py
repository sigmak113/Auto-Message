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
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")

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
PRIMARY_TINT = "#E6F9F3"  # 선택된 항목 배경(연한 민트)
HEADER_BG = "#1B2733"
DANGER_BG = "#FDEDED"
DANGER_FG = "#C0392B"
DANGER_HOVER = "#FAD4D4"
NEUTRAL_BG = "#EEF0F3"
NEUTRAL_HOVER = "#E2E5EA"

BADGE_COLORS = ["#00B894", "#0984E3", "#6C5CE7", "#E17055", "#E84393", "#00B8D9"]

FONT_BASE = ("맑은 고딕", 10)
FONT_SECTION = ("맑은 고딕", 11, "bold")
FONT_LABEL = ("맑은 고딕", 9, "bold")
FONT_HEADER = ("맑은 고딕", 12, "bold")
FONT_BTN = ("맑은 고딕", 10, "bold")

BTN_HEIGHT = 40  # 추가/수정/삭제/복사 버튼 공통 높이

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


def _rounded_points(x1, y1, x2, y2, r):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


# ------------------------------------------------------------------
# 둥근 모서리 버튼 (Canvas 기반, 실제 rounded-rect를 그림)
# ------------------------------------------------------------------
class RoundedButton(tk.Frame):
    def __init__(
        self, parent, text, command, bg, fg, hover_bg=None,
        height=BTN_HEIGHT, radius=10, font=FONT_BTN, parent_bg=None,
    ):
        parent_bg = parent_bg or parent["bg"]
        super().__init__(parent, bg=parent_bg, height=height)
        self.pack_propagate(False)
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg or bg
        self.fg = fg
        self.radius = radius
        self.font = font
        self.text = text
        self._current = bg

        self.canvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw(self._current))
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", lambda e: self._draw(self.hover_color))
        self.canvas.bind("<Leave>", lambda e: self._draw(self.bg_color))

    def _draw(self, color):
        self._current = color
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 4 or h < 4:
            return
        self.canvas.delete("all")
        pts = _rounded_points(1, 1, w - 1, h - 1, self.radius)
        self.canvas.create_polygon(pts, smooth=True, fill=color, outline=color)
        self.canvas.create_text(
            w / 2, h / 2, text=self.text, fill=self.fg, font=self.font
        )

    def _on_click(self, event):
        if self.command:
            self.command()


# ------------------------------------------------------------------
# 둥근 모서리 카드 (Canvas 배경 + 내부 콘텐츠 프레임)
# ------------------------------------------------------------------
class RoundedCard(tk.Frame):
    def __init__(self, parent, radius=16, bg=CARD, border=BORDER, parent_bg=None, **kwargs):
        parent_bg = parent_bg or parent["bg"]
        super().__init__(parent, bg=parent_bg, **kwargs)
        self.radius = radius
        self.bg_color = bg
        self.border_color = border
        self.canvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.content = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window(10, 10, anchor="nw", window=self.content)
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        w, h = event.width, event.height
        if w < 4 or h < 4:
            return
        self.canvas.delete("bg")
        pts = _rounded_points(1, 1, w - 1, h - 1, self.radius)
        self.canvas.create_polygon(
            pts, smooth=True, fill=self.bg_color, outline=self.border_color, tags="bg"
        )
        self.canvas.tag_lower("bg")
        self.canvas.coords(self._window, 10, 10)
        self.canvas.itemconfigure(self._window, width=max(0, w - 20), height=max(0, h - 20))


# ------------------------------------------------------------------
# 템플릿 추가/수정 다이얼로그
# ------------------------------------------------------------------
class TemplateEditDialog(tk.Toplevel):
    def __init__(self, parent, name="", body=""):
        super().__init__(parent)
        self.title("템플릿 편집")
        self.geometry("620x560")
        self.minsize(480, 380)
        self.configure(bg=BG)
        self.result = None
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 20, "pady": (16, 4)}

        # ── 항상 화면에 보이는 하단 버튼 영역을 '먼저' side=bottom 으로 고정 ──
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=16)
        save_holder = tk.Frame(btn_frame, bg=BG, width=100, height=BTN_HEIGHT)
        save_holder.pack_propagate(False)
        save_holder.pack(side="right")
        RoundedButton(
            save_holder, "저장", self._on_save, bg=PRIMARY, fg="white",
            hover_bg=PRIMARY_DARK, height=BTN_HEIGHT, radius=10, parent_bg=BG,
        ).pack(fill="both", expand=True)
        cancel_holder = tk.Frame(btn_frame, bg=BG, width=100, height=BTN_HEIGHT)
        cancel_holder.pack_propagate(False)
        cancel_holder.pack(side="right", padx=(0, 8))
        RoundedButton(
            cancel_holder, "취소", self.destroy, bg=NEUTRAL_BG, fg=TEXT_MAIN,
            hover_bg=NEUTRAL_HOVER, height=BTN_HEIGHT, radius=10, parent_bg=BG,
        ).pack(fill="both", expand=True)

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

        body_card = RoundedCard(self, radius=12, bg=CARD, border=BORDER, parent_bg=BG)
        body_card.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        body_inner = body_card.content
        self.body_text = tk.Text(
            body_inner, font=FONT_BASE, wrap="word", relief="flat",
            bg=CARD, fg=TEXT_MAIN,
        )
        scroll = tk.Scrollbar(body_inner, command=self.body_text.yview)
        self.body_text.configure(yscrollcommand=scroll.set)
        self.body_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.body_text.insert("1.0", body)

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
        self.template_row_widgets = []  # (outer_frame, inner_frame) per template row

        self._apply_icon()
        self._build_layout()
        self._refresh_template_list()

    # ---------------- 아이콘 ----------------
    def _apply_icon(self):
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except tk.TclError:
                pass

    # ---------------- UI 구성 ----------------
    def _build_layout(self):
        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(fill="both", expand=True)

        # 왼쪽: 템플릿 목록 -------------------------------------------------
        left = RoundedCard(root_frame, radius=16, width=280, parent_bg=BG)
        left.pack(side="left", fill="y", padx=(16, 8), pady=16)
        left.pack_propagate(False)
        left_content = left.content

        tk.Label(
            left_content, text="템플릿 목록", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", pady=(4, 8))

        list_area = tk.Frame(left_content, bg=CARD)
        list_area.pack(fill="both", expand=True)

        list_canvas = tk.Canvas(list_area, bg=CARD, highlightthickness=0)
        list_scroll = tk.Scrollbar(list_area, command=list_canvas.yview)
        self.template_list_frame = tk.Frame(list_canvas, bg=CARD)
        self.template_list_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")),
        )
        list_canvas.create_window((0, 0), window=self.template_list_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=list_scroll.set)
        list_canvas.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")

        btns = tk.Frame(left_content, bg=CARD)
        btns.pack(fill="x", pady=(12, 4))
        btns.columnconfigure((0, 1, 2), weight=1, uniform="tmplbtn")
        btns.rowconfigure(0, minsize=BTN_HEIGHT)

        add_holder = tk.Frame(btns, bg=CARD, height=BTN_HEIGHT)
        add_holder.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        RoundedButton(
            add_holder, "＋ 추가", self._add_template, bg=PRIMARY, fg="white",
            hover_bg=PRIMARY_DARK, height=BTN_HEIGHT, radius=10, parent_bg=CARD,
        ).pack(fill="both", expand=True)

        edit_holder = tk.Frame(btns, bg=CARD, height=BTN_HEIGHT)
        edit_holder.grid(row=0, column=1, sticky="nsew", padx=4)
        RoundedButton(
            edit_holder, "수정", self._edit_template, bg=NEUTRAL_BG, fg=TEXT_MAIN,
            hover_bg=NEUTRAL_HOVER, height=BTN_HEIGHT, radius=10, parent_bg=CARD,
        ).pack(fill="both", expand=True)

        del_holder = tk.Frame(btns, bg=CARD, height=BTN_HEIGHT)
        del_holder.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        RoundedButton(
            del_holder, "삭제", self._delete_template, bg=DANGER_BG, fg=DANGER_FG,
            hover_bg=DANGER_HOVER, height=BTN_HEIGHT, radius=10, parent_bg=CARD,
        ).pack(fill="both", expand=True)

        # 가운데: 항목 입력 ---------------------------------------------------
        mid = RoundedCard(root_frame, radius=16, width=310, parent_bg=BG)
        mid.pack(side="left", fill="both", padx=8, pady=16)
        mid.pack_propagate(False)
        mid_content = mid.content

        tk.Label(
            mid_content, text="변경할 항목 입력", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", pady=(4, 8))

        fields_area = tk.Frame(mid_content, bg=CARD)
        fields_area.pack(fill="both", expand=True)

        canvas = tk.Canvas(fields_area, highlightthickness=0, bg=CARD)
        vscroll = tk.Scrollbar(fields_area, orient="vertical", command=canvas.yview)
        self.fields_frame = tk.Frame(canvas, bg=CARD)
        self.fields_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.fields_frame, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        gen_holder = tk.Frame(mid_content, bg=CARD, height=BTN_HEIGHT)
        gen_holder.pack_propagate(False)
        gen_holder.pack(fill="x", pady=(12, 4))
        RoundedButton(
            gen_holder, "메세지 생성 ▶", self._generate_message, bg=PRIMARY_DARK,
            fg="white", hover_bg=PRIMARY, height=BTN_HEIGHT, radius=10, parent_bg=CARD,
        ).pack(fill="both", expand=True)

        # 오른쪽: 미리보기 -----------------------------------------------------
        right = RoundedCard(root_frame, radius=16, parent_bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(8, 16), pady=16)
        right_content = right.content

        tk.Label(
            right_content, text="미리보기", font=FONT_SECTION, bg=CARD, fg=TEXT_MAIN,
        ).pack(anchor="w", pady=(4, 8))

        preview_frame = tk.Frame(right_content, bg=CARD)
        preview_frame.pack(fill="both", expand=True)
        self.preview_text = tk.Text(
            preview_frame, font=("맑은 고딕", 11), wrap="word", state="disabled",
            relief="flat", bg="#F8F9FB", fg=TEXT_MAIN, padx=14, pady=14,
            highlightthickness=1, highlightbackground=BORDER,
        )
        preview_scroll = tk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        copy_holder = tk.Frame(right_content, bg=CARD, height=BTN_HEIGHT)
        copy_holder.pack_propagate(False)
        copy_holder.pack(fill="x", pady=(12, 4))
        RoundedButton(
            copy_holder, "📋  클립보드로 복사", self._copy_to_clipboard, bg=PRIMARY,
            fg="white", hover_bg=PRIMARY_DARK, height=BTN_HEIGHT, radius=10, parent_bg=CARD,
        ).pack(fill="both", expand=True)

        self.status_label = tk.Label(
            right_content, text="", fg=TEXT_SUB, bg=CARD, font=("맑은 고딕", 9)
        )
        self.status_label.pack(anchor="w", pady=(6, 4))

    # ---------------- 템플릿 목록 로직 ----------------
    def _refresh_template_list(self, keep_selection=True):
        prev = self.selected_index
        save_templates(self.templates)

        if keep_selection and prev is not None and prev < len(self.templates):
            new_index = prev
        elif self.templates:
            new_index = 0
        else:
            new_index = None

        self._render_template_rows(new_index)

        if new_index is not None:
            self._load_fields_for(new_index)
        else:
            self._clear_fields()

    def _render_template_rows(self, active_index):
        self.selected_index = active_index
        for w in self.template_list_frame.winfo_children():
            w.destroy()
        self.template_row_widgets = []

        for idx, t in enumerate(self.templates):
            selected = (idx == active_index)
            border_color = PRIMARY if selected else BORDER
            row_bg = PRIMARY_TINT if selected else CARD

            outer = tk.Frame(self.template_list_frame, bg=border_color, cursor="hand2")
            outer.pack(fill="x", pady=4)
            inner_pad = 2 if selected else 1
            inner = tk.Frame(outer, bg=row_bg)
            inner.pack(fill="both", expand=True, padx=inner_pad, pady=inner_pad)

            badge_color = BADGE_COLORS[idx % len(BADGE_COLORS)]
            badge = tk.Canvas(inner, width=26, height=26, bg=row_bg, highlightthickness=0)
            badge.pack(side="left", padx=(10, 8), pady=9)
            badge.create_oval(1, 1, 25, 25, fill=badge_color, outline=badge_color)
            badge.create_text(
                13, 13, text=str(idx + 1), fill="white", font=("맑은 고딕", 9, "bold")
            )

            name_label = tk.Label(
                inner, text=t["name"], bg=row_bg, fg=TEXT_MAIN, font=FONT_BASE,
                anchor="w", justify="left", wraplength=190,
            )
            name_label.pack(side="left", fill="x", expand=True, pady=9, padx=(0, 8))

            for widget in (outer, inner, badge, name_label):
                widget.bind("<Button-1>", lambda e, i=idx: self._select_template(i))

            self.template_row_widgets.append(outer)

    def _select_template(self, index):
        if index == self.selected_index:
            return
        self._render_template_rows(index)
        self._load_fields_for(index)

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
            ).pack(anchor="w", pady=8)
        else:
            for name in placeholders:
                tk.Label(
                    self.fields_frame, text=name, font=FONT_LABEL,
                    bg=CARD, fg=TEXT_MAIN,
                ).pack(anchor="w", pady=(10, 3))

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
                entry.pack(anchor="w", fill="x", ipady=5)
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
            new_idx = len(self.templates) - 1
            self._render_template_rows(new_idx)
            self._load_fields_for(new_idx)

    def _edit_template(self):
        if self.selected_index is None:
            messagebox.showinfo("확인", "수정할 템플릿을 먼저 선택해주세요.")
            return
        idx = self.selected_index
        t = self.templates[idx]
        dlg = TemplateEditDialog(self, name=t["name"], body=t["body"])
        self.wait_window(dlg)
        if dlg.result:
            self.templates[idx] = dlg.result
            self._render_template_rows(idx)
            save_templates(self.templates)
            self._load_fields_for(idx)

    def _delete_template(self):
        if self.selected_index is None:
            messagebox.showinfo("확인", "삭제할 템플릿을 먼저 선택해주세요.")
            return
        idx = self.selected_index
        if messagebox.askyesno(
            "삭제 확인", f"'{self.templates[idx]['name']}' 템플릿을 삭제할까요?"
        ):
            del self.templates[idx]
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
