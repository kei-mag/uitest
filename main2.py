import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os
import re

# --- 設定と定数 ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppColors:
    # --- ブランドカラー調整版 ---
    # 企業HPの青を意識しつつ、業務アプリ用に少し彩度を落とした深めのネイビー
    BRAND_BLUE = "#1e3a8a"       # メインヘッダー、強調色 (Dark Blue)
    BRAND_BLUE_HOVER = "#172554" # ホバー時の色
    
    # 企業HPの赤を意識したアクセントカラー
    BRAND_RED = "#dc2626"        # ロゴ背景、バッジ、強調 (Red 600)
    
    # ベースカラー（目に優しい配色）
    BG_LIGHT = "#f8fafc"         # 背景（白に近いグレー）
    BG_DARK = "#0f172a"          # ダークモード背景
    
    # テキストカラー
    TEXT_HEADER = "#ffffff"      # ヘッダー文字は白
    
    # アクションカラー
    ACTION_SAVE = "#059669"      # 保存ボタンなどは安心感のある緑（Emerald）

# --- データ生成 (ダミー) ---
def generate_dummy_data():
    categories = ['半導体', '電子部品', '電気部品', 'コネクター', '開発ツール']
    ranks = ['S', 'A', 'B', 'C', 'J']
    data = []
    for i in range(20):
        id_str = str(i + 1).zfill(4)
        category = categories[i % len(categories)]
        rank = ranks[i % len(ranks)]
        item = {
            "id": id_str,
            "webcd": id_str,
            "name": f"{category} - 部品型番{id_str}",
            "catch_copy": f"高信頼性・長寿命の{category}です。在庫即納可能です。",
            "jan": f"4901234{str(i).zfill(6)}",
            "instore_jan": f"20000000{str(i).zfill(4)}",
            "cost_price": str(100 + (i * 10)),
            "selling_price": str(250 + (i * 20)),
            "tax_rate": "10%",
            "stock_quantity": str(i * 50),
            "rank": rank,
            "delivery": "即日" if i % 2 == 0 else "3営業日",
            "delivery_display": "即納" if i % 2 == 0 else "取寄",
            "shelf": f"{chr(65 + (i % 3))}-{str(i % 5).zfill(2)}",
            "size_w": "10",
            "size_h": "5",
            "size_d": "2",
            "weight": "5",
            "is_published": True,
            "is_sale": False,
            "is_free_shipping": i % 10 == 0,
            "memo": f"ロット管理No.{id_str}",
            "description": f"<h2>{category} {id_str} 仕様書</h2>\n<p><strong>定格電圧:</strong> 5.0V<br><strong>許容差:</strong> ±1%</p>\n<ul>\n<li>RoHS対応</li>\n<li>産業機器向け</li>\n</ul>"
        }
        data.append(item)
    return data

# --- UI コンポーネント ---

class SectionTitle(ctk.CTkFrame):
    """セクションタイトル：企業の青をアクセントに使用"""
    def __init__(self, master, title, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # アクセントバーをブランドブルーに
        self.bar = ctk.CTkFrame(self, width=5, height=20, fg_color=AppColors.BRAND_BLUE, corner_radius=2)
        self.bar.grid(row=0, column=0, padx=(0, 5), pady=10)
        
        self.label = ctk.CTkLabel(self, text=title, font=("Meiryo UI", 14, "bold"))
        self.label.grid(row=0, column=1, sticky="w")
        
        self.separator = ctk.CTkFrame(self, height=2, fg_color=("gray80", "gray30"))
        self.separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

class InputField(ctk.CTkFrame):
    def __init__(self, master, label, value_var, width=None, readonly=False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(self, text=label, font=("Meiryo UI", 11, "bold"), text_color=("gray50", "gray40"), anchor="w")
        self.label.pack(fill="x", pady=(0, 2))
        
        state = "readonly" if readonly else "normal"
        fg_color = ("#f1f5f9", "#334155") if readonly else None
        
        self.entry = ctk.CTkEntry(self, textvariable=value_var, state=state, fg_color=fg_color, height=32, font=("Meiryo UI", 13))
        if width: self.entry.configure(width=width)
        self.entry.pack(fill="x")

class CheckBoxField(ctk.CTkFrame):
    def __init__(self, master, label, variable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        # チェックボックスの色もブランドブルーに合わせる
        self.check = ctk.CTkCheckBox(self, text=label, variable=variable, font=("Meiryo UI", 12), fg_color=AppColors.BRAND_BLUE, hover_color=AppColors.BRAND_BLUE_HOVER)
        self.check.pack(anchor="w", pady=5)

class EditorView(ctk.CTkFrame):
    def __init__(self, master, data, icons, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.data = data
        self.icons = icons
        self.active_id = data[0]["id"]
        self.vars = {}
        
        # タブコンテナ: 背景色は淡い色、ボーダーで区切る
        self.tab_container = ctk.CTkScrollableFrame(self, height=45, orientation="horizontal", fg_color=("gray95", "gray15"), corner_radius=0)
        self.tab_container.pack(fill="x", side="top")
        
        self.tabs = {}
        self.refresh_tabs()

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)
        
        self.create_form_content()
        self.load_active_item()

    def refresh_tabs(self):
        for widget in self.tab_container.winfo_children():
            widget.destroy()
            
        for item in self.data:
            is_active = item["id"] == self.active_id
            
            # アクティブタブ: 白背景、ブランドブルーの文字と枠線
            fg_color = ("white", "gray25") if is_active else "transparent"
            text_color = (AppColors.BRAND_BLUE, "#60a5fa") if is_active else ("gray40", "gray50")
            border_width = 2 if is_active else 0
            border_color = AppColors.BRAND_BLUE
            
            btn = ctk.CTkButton(
                self.tab_container,
                text=item["name"],
                image=self.icons.get("box"),
                compound="left",
                width=180,
                height=34,
                corner_radius=6,
                fg_color=fg_color,
                text_color=text_color,
                border_width=border_width,
                border_color=border_color,
                hover_color=("gray90", "gray30"),
                anchor="w",
                font=("Meiryo UI", 12, "bold" if is_active else "normal"),
                command=lambda i=item["id"]: self.switch_tab(i)
            )
            btn.pack(side="left", padx=3, pady=5)

    def switch_tab(self, new_id):
        self.save_current_values()
        self.active_id = new_id
        self.refresh_tabs()
        self.load_active_item()

    def create_form_content(self):
        self.content_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=20, pady=20, expand=True)
        
        # --- 基本情報 ---
        SectionTitle(self.content_frame, title="基本情報").pack(fill="x")
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        self.vars["webcd"] = ctk.StringVar()
        self.vars["name"] = ctk.StringVar()
        self.vars["catch_copy"] = ctk.StringVar()
        
        InputField(row1, "!WebCD", self.vars["webcd"], width=100).pack(side="left", padx=(0, 10))
        InputField(row1, "!商品名", self.vars["name"]).pack(side="left", fill="x", expand=True)
        InputField(self.content_frame, "キャッチコピー", self.vars["catch_copy"]).pack(fill="x", pady=5)

        # --- コード・価格・在庫 ---
        SectionTitle(self.content_frame, title="コード・価格・在庫").pack(fill="x", pady=(20, 0))
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(fill="x", pady=5)
        grid_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        keys = ["jan", "instore_jan", "id", "cost_price", "selling_price", "tax_rate", "stock_quantity"]
        for k in keys: self.vars[k] = ctk.StringVar()
        
        InputField(grid_frame, "!JANコード", self.vars["jan"]).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "インストアJAN", self.vars["instore_jan"]).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "仕入先コード", self.vars["id"], readonly=True).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "原価", self.vars["cost_price"]).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "売価", self.vars["selling_price"]).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "税率", self.vars["tax_rate"]).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "在庫数", self.vars["stock_quantity"]).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # --- 物流・管理 ---
        SectionTitle(self.content_frame, title="物流・管理情報").pack(fill="x", pady=(20, 0))
        logi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        logi_frame.pack(fill="x")
        logi_frame.grid_columnconfigure((0,1,2,3), weight=1)

        keys_logi = ["delivery", "delivery_display", "shelf", "rank", "size_w", "size_h", "size_d", "weight"]
        for k in keys_logi: self.vars[k] = ctk.StringVar()

        InputField(logi_frame, "納期", self.vars["delivery"]).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "納期表示", self.vars["delivery_display"]).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "棚番号", self.vars["shelf"]).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "品質ランク", self.vars["rank"]).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        size_bg = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray25"))
        size_bg.pack(fill="x", pady=10)
        size_bg.grid_columnconfigure((0,1,2,3), weight=1)
        InputField(size_bg, "幅 (mm)", self.vars["size_w"]).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "高さ (mm)", self.vars["size_h"]).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "奥行 (mm)", self.vars["size_d"]).grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "重量 (g)", self.vars["weight"]).grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # --- 設定・フラグ & メモ ---
        two_col = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        two_col.pack(fill="x", pady=10)
        two_col.grid_columnconfigure((0, 1), weight=1)

        flag_frame = ctk.CTkFrame(two_col, fg_color="transparent")
        flag_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        SectionTitle(flag_frame, title="設定・フラグ").pack(fill="x")
        
        self.vars["is_published"] = ctk.BooleanVar()
        self.vars["is_sale"] = ctk.BooleanVar()
        self.vars["is_free_shipping"] = ctk.BooleanVar()
        CheckBoxField(flag_frame, "Web公開する", self.vars["is_published"]).pack(anchor="w")
        CheckBoxField(flag_frame, "セール対象", self.vars["is_sale"]).pack(anchor="w")
        CheckBoxField(flag_frame, "送料無料", self.vars["is_free_shipping"]).pack(anchor="w")

        memo_frame = ctk.CTkFrame(two_col, fg_color="transparent")
        memo_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        SectionTitle(memo_frame, title="社内用メモ").pack(fill="x")
        self.memo_text = ctk.CTkTextbox(memo_frame, height=80, font=("Meiryo UI", 12))
        self.memo_text.pack(fill="x", pady=5)

        # --- エディタ ---
        SectionTitle(self.content_frame, title="商品説明").pack(fill="x", pady=(20, 5))
        editor_container = ctk.CTkFrame(self.content_frame, border_width=1, border_color=("gray70", "gray40"))
        editor_container.pack(fill="x", pady=5)
        
        editor_header = ctk.CTkFrame(editor_container, height=30, fg_color=("gray95", "gray20"), corner_radius=0)
        editor_header.pack(fill="x")
        ctk.CTkLabel(editor_header, text="HTML Source", font=("Consolas", 10, "bold"), text_color="gray").pack(side="left", padx=10)
        ctk.CTkLabel(editor_header, text="Preview (Text)", font=("Meiryo UI", 10), text_color="gray").pack(side="right", padx=10)

        split_body = ctk.CTkFrame(editor_container, fg_color="transparent")
        split_body.pack(fill="x")
        split_body.grid_columnconfigure((0, 1), weight=1)
        
        self.desc_source = ctk.CTkTextbox(split_body, height=200, font=("Consolas", 12), wrap="none")
        self.desc_source.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.desc_source.bind("<KeyRelease>", self.update_preview)
        
        self.desc_preview = ctk.CTkTextbox(split_body, height=200, font=("Meiryo UI", 13), fg_color=("white", "gray15"), state="disabled")
        self.desc_preview.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def load_active_item(self):
        item = next((i for i in self.data if i["id"] == self.active_id), None)
        if not item: return
        for key, var in self.vars.items():
            if key in item:
                val = item[key]
                if isinstance(var, ctk.BooleanVar): var.set(bool(val))
                else: var.set(str(val))
        self.memo_text.delete("1.0", "end"); self.memo_text.insert("1.0", item.get("memo", ""))
        self.desc_source.delete("1.0", "end"); self.desc_source.insert("1.0", item.get("description", ""))
        self.update_preview()

    def save_current_values(self):
        item = next((i for i in self.data if i["id"] == self.active_id), None)
        if not item: return
        for key, var in self.vars.items(): item[key] = var.get()
        item["memo"] = self.memo_text.get("1.0", "end-1c")
        item["description"] = self.desc_source.get("1.0", "end-1c")

    def update_preview(self, event=None):
        html_content = self.desc_source.get("1.0", "end-1c")
        text_content = html_content.replace("<br>", "\n").replace("</p>", "\n\n").replace("</li>", "\n")
        text_content = re.sub(r'<li>', '・ ', text_content)
        text_content = re.sub(r'<[^>]+>', '', text_content)
        self.desc_preview.configure(state="normal")
        self.desc_preview.delete("1.0", "end")
        self.desc_preview.insert("1.0", text_content)
        self.desc_preview.configure(state="disabled")

class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, on_back, icons, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_back = on_back
        self.icons = icons
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        back_btn = ctk.CTkButton(header, text="戻る", image=icons.get("back"), width=80, fg_color="transparent", border_width=1, text_color=("gray20", "gray80"), command=on_back)
        back_btn.pack(side="left")
        ctk.CTkLabel(header, text="設定", font=("Meiryo UI", 24, "bold")).pack(side="left", padx=20)
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=40, pady=10)
        
        info_card = ctk.CTkFrame(content, corner_radius=15)
        info_card.pack(fill="x", pady=20)
        
        # モチーフ: カード上部に企業の「青・赤・白」のトリコロールバーを表示
        bar_frame = ctk.CTkFrame(info_card, height=6, corner_radius=6, fg_color="transparent")
        bar_frame.pack(fill="x")
        # 左(青) 中(白) 右(赤) でモチーフを表現
        bar_blue = ctk.CTkFrame(bar_frame, height=6, fg_color=AppColors.BRAND_BLUE, width=100, corner_radius=0)
        bar_blue.pack(side="left", fill="x", expand=True)
        bar_white = ctk.CTkFrame(bar_frame, height=6, fg_color="white", width=20, corner_radius=0)
        bar_white.pack(side="left")
        bar_red = ctk.CTkFrame(bar_frame, height=6, fg_color=AppColors.BRAND_RED, width=50, corner_radius=0)
        bar_red.pack(side="left")

        ctk.CTkLabel(info_card, text="eltex CSV Editor", font=("Meiryo UI", 20, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(info_card, text="Version 1.2.1 (Corporate Ed.)", text_color="gray").pack(pady=(0, 20))

        self.create_settings_section(content, "一般設定", [
            ("テーマ", self.create_theme_selector),
            ("言語", lambda p: ctk.CTkOptionMenu(p, values=["日本語", "English"]).pack(anchor="e")),
        ])
        self.create_settings_section(content, "AI 機能設定", [
            ("AIモデル", lambda p: ctk.CTkOptionMenu(p, values=["gpt-4o", "gemini-1.5-pro"]).pack(anchor="e")),
            ("APIキー", lambda p: ctk.CTkEntry(p, show="*", width=300, placeholder_text="sk-...").pack(anchor="e"))
        ])

    def create_settings_section(self, parent, title, items):
        ctk.CTkLabel(parent, text=title, font=("Meiryo UI", 12, "bold"), text_color="gray").pack(anchor="w", pady=(20, 5))
        container = ctk.CTkFrame(parent, fg_color=("white", "gray20"))
        container.pack(fill="x")
        for i, (label, widget_factory) in enumerate(items):
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=15)
            ctk.CTkLabel(row, text=label, font=("Meiryo UI", 13)).pack(side="left")
            widget_factory(row)
            if i < len(items) - 1: ctk.CTkFrame(container, height=1, fg_color=("gray90", "gray30")).pack(fill="x")

    def create_theme_selector(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="right")
        modes = ["Light", "Dark", "System"]
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        def change_theme(mode): ctk.set_appearance_mode(mode)
        for mode in modes:
            ctk.CTkRadioButton(frame, text=mode, variable=self.theme_var, value=mode, command=lambda m=mode: change_theme(m)).pack(side="left", padx=5)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("eltex CSV Editor - Corporate Edition")
        self.geometry("1200x800")
        
        self.icons = self.load_icons()
        self.data = generate_dummy_data()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_header()
        
        self.editor_view = EditorView(self, self.data, self.icons)
        self.settings_view = SettingsView(self, self.show_editor, self.icons)
        self.show_editor()

    def load_icons(self):
        icons = {}
        icon_defs = {
            "app": "assets/app_icon.png", "save": "assets/save.png", "settings": "assets/settings.png",
            "box": "assets/box.png", "github": "assets/github.png", "web": "assets/globe.png", "back": "assets/chevron-left.png"
        }
        for name, path in icon_defs.items():
            if os.path.exists(path):
                try:
                    pil_image = Image.open(path)
                    icons[name] = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(20, 20))
                except: icons[name] = None
            else: icons[name] = None
        return icons

    def create_header(self):
        # ヘッダー背景を「コーポレート・ブルー」に設定
        header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=AppColors.BRAND_BLUE)
        header.grid(row=0, column=0, sticky="ew")
        
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=15, pady=10)
        
        # ロゴアクセント: ブランドの「赤」をワンポイントで使用（企業のロゴ背景イメージ）
        logo_box = ctk.CTkFrame(title_frame, width=32, height=32, fg_color=AppColors.BRAND_RED, corner_radius=4)
        logo_box.pack(side="left", padx=(0, 10))
        # ロゴの中に白い文字風の装飾（'el'とか）を入れるのも良いが、ここではシンプルに
        
        ctk.CTkLabel(title_frame, text="eltex CSV Editor", font=("Meiryo UI", 16, "bold"), text_color=AppColors.TEXT_HEADER).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)
        
        self.status_label = ctk.CTkLabel(btn_frame, text=f"Data: {len(self.data)} items", text_color="#bfdbfe", font=("Meiryo UI", 12))
        self.status_label.pack(side="left", padx=15)
        
        # 保存ボタンは視認性重視でグリーン、設定ボタンはヘッダーに馴染む色
        ctk.CTkButton(btn_frame, text="保存", image=self.icons.get("save"), width=100, fg_color=AppColors.ACTION_SAVE, hover_color="#047857", command=self.on_save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="", image=self.icons.get("settings"), width=40, fg_color="transparent", hover_color=AppColors.BRAND_BLUE_HOVER, command=self.show_settings).pack(side="left", padx=5)

    def show_editor(self):
        self.settings_view.grid_forget()
        self.editor_view.grid(row=1, column=0, sticky="nsew")

    def show_settings(self):
        self.editor_view.grid_forget()
        self.settings_view.grid(row=1, column=0, sticky="nsew")

    def on_save(self):
        self.editor_view.save_current_values()
        messagebox.showinfo("Export", "CSV Export Successful (Demo)")

if __name__ == "__main__":
    app = App()
    app.mainloop()

