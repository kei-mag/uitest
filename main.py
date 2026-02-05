import os
import re
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

# --- 設定と定数 ---
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class AppColors:
    # TailwindのSlate系カラーに近い色を定義
    BG_LIGHT = "#f8fafc" # slate-50
    BG_DARK = "#0f172a"  # slate-950
    HEADER_LIGHT = "#1e293b" # slate-800
    HEADER_DARK = "#020617" # slate-950 darker
    SIDEBAR_LIGHT = "#e2e8f0" # slate-200
    SIDEBAR_DARK = "#1e293b" # slate-800
    ACCENT = "#2563eb" # blue-600

# --- データ生成 (ダミー) ---
def generate_dummy_data():
    categories = ['家電', '家具', 'オーディオ', 'キッチン', 'ステーショナリー']
    ranks = ['S', 'A', 'B', 'C', 'J']
    data = []
    for i in range(20):
        id_str = str(i + 1).zfill(4)
        category = categories[i % len(categories)]
        rank = ranks[i % len(ranks)]
        item = {
            "id": id_str,
            "webcd": id_str,
            "name": f"商品アイテム {category} - {id_str}番",
            "catch_copy": f"この{category}は大変お買い得な一品です。機能性抜群。",
            "jan": f"4901234{str(i).zfill(6)}",
            "instore_jan": f"20000000{str(i).zfill(4)}",
            "cost_price": str(1000 + (i * 100)),
            "selling_price": str(1980 + (i * 200)),
            "tax_rate": "10%",
            "stock_quantity": str(i * 5),
            "rank": rank,
            "delivery": f"{(i % 3) + 1}日",
            "delivery_display": "即納" if i % 2 == 0 else "取寄",
            "shelf": f"{chr(65 + (i % 5))}-{str(i % 10).zfill(2)}",
            "size_w": str(100 + (i * 10)),
            "size_h": str(200 + (i * 5)),
            "size_d": str(50 + (i * 2)),
            "weight": str(500 + (i * 50)),
            "is_published": i % 3 != 0,
            "is_sale": i % 5 == 0,
            "is_free_shipping": i % 2 == 0,
            "memo": f"テスト用データ{id_str}です。\nPython Tkinterでの動作確認用。",
            "description": f"<h2>{category} {id_str} の詳細</h2>\n<p>これは自動生成されたテストデータです。<strong>{id_str}番目</strong>の商品です。</p>\n<ul>\n<li>特徴1: 高品質な{category}</li>\n<li>特徴2: 安心の{rank}ランク</li>\n</ul>"
        }
        data.append(item)
    return data

# --- UI コンポーネント ---

class SectionTitle(ctk.CTkFrame):
    """セクションタイトルコンポーネント"""
    def __init__(self, master, title, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        self.bar = ctk.CTkFrame(self, width=5, height=20, fg_color=AppColors.ACCENT, corner_radius=2)
        self.bar.grid(row=0, column=0, padx=(0, 5), pady=10)
        
        self.label = ctk.CTkLabel(self, text=title, font=("Meiryo UI", 14, "bold"))
        self.label.grid(row=0, column=1, sticky="w")
        
        self.separator = ctk.CTkFrame(self, height=2, fg_color=("gray80", "gray30"))
        self.separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

class InputField(ctk.CTkFrame):
    """ラベル付き入力フィールド"""
    def __init__(self, master, label, value_var, width=None, readonly=False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.label = ctk.CTkLabel(self, text=label, font=("Meiryo UI", 11, "bold"), text_color=("gray50", "gray40"), anchor="w")
        self.label.pack(fill="x", pady=(0, 2))
        
        state = "readonly" if readonly else "normal"
        fg_color = ("#f1f5f9", "#334155") if readonly else None
        
        self.entry = ctk.CTkEntry(self, textvariable=value_var, state=state, fg_color=fg_color, height=32, font=("Meiryo UI", 13))
        if width:
            self.entry.configure(width=width)
        self.entry.pack(fill="x")

class CheckBoxField(ctk.CTkFrame):
    """チェックボックスラッパー"""
    def __init__(self, master, label, variable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.check = ctk.CTkCheckBox(self, text=label, variable=variable, font=("Meiryo UI", 12))
        self.check.pack(anchor="w", pady=5)

class EditorView(ctk.CTkFrame):
    """エディタ画面"""
    def __init__(self, master, data, icons, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.data = data
        self.icons = icons
        self.active_id = data[0]["id"]
        self.vars = {} # 現在編集中の変数を保持
        
        # --- レイアウト ---
        # 1. タブエリア (上部)
        self.tab_container = ctk.CTkScrollableFrame(self, height=40, orientation="horizontal", fg_color=("gray90", "gray20"), corner_radius=0)
        self.tab_container.pack(fill="x", side="top")
        
        self.tabs = {}
        self.refresh_tabs()

        # 2. メインフォーム (スクロール可能)
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)
        
        self.create_form_content()
        self.load_active_item()

    def refresh_tabs(self):
        # 既存のタブをクリア (再描画コスト削減のため本来は差分更新が良いが簡易実装)
        for widget in self.tab_container.winfo_children():
            widget.destroy()
            
        for item in self.data:
            is_active = item["id"] == self.active_id
            
            # アクティブなタブと非アクティブなタブのデザイン切り替え
            fg_color = ("white", "gray30") if is_active else "transparent"
            text_color = (AppColors.ACCENT, "#60a5fa") if is_active else ("gray40", "gray50")
            border_width = 2 if is_active else 0
            # border_colorにtransparentを指定するとエラーになるため、常に色を指定する（width=0なら見えない）
            border_color = AppColors.ACCENT
            
            btn = ctk.CTkButton(
                self.tab_container,
                text=item["name"],
                image=self.icons.get("box"),
                compound="left",
                width=180,
                height=32,
                corner_radius=6,
                fg_color=fg_color,
                text_color=text_color,
                border_width=border_width,
                border_color=border_color,
                hover_color=("gray85", "gray25"),
                anchor="w",
                command=lambda i=item["id"]: self.switch_tab(i)
            )
            btn.pack(side="left", padx=2, pady=5)

    def switch_tab(self, new_id):
        # 現在の値を保存
        self.save_current_values()
        self.active_id = new_id
        self.refresh_tabs()
        self.load_active_item()

    def create_form_content(self):
        # フォームの中身を構築 (変数は後でセット)
        self.content_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=20, pady=20, expand=True)
        
        # --- 基本情報 ---
        SectionTitle(self.content_frame, title="基本情報").pack(fill="x")
        
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        # 変数初期化
        self.vars["webcd"] = ctk.StringVar()
        self.vars["name"] = ctk.StringVar()
        self.vars["catch_copy"] = ctk.StringVar()
        
        InputField(row1, "!WebCD", self.vars["webcd"], width=100).pack(side="left", padx=(0, 10))
        InputField(row1, "!商品名", self.vars["name"]).pack(side="left", fill="x", expand=True)
        
        InputField(self.content_frame, "キャッチコピー", self.vars["catch_copy"]).pack(fill="x", pady=5)

        # --- コード・価格・在庫 (グリッド風) ---
        # 修正: mt引数は存在しないため、padyを使用
        SectionTitle(self.content_frame, title="コード・価格・在庫").pack(fill="x", pady=(10, 0))
        
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(fill="x", pady=5)
        # 簡易的なGrid配置 (4列)
        grid_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.vars["jan"] = ctk.StringVar()
        self.vars["instore_jan"] = ctk.StringVar()
        self.vars["id"] = ctk.StringVar()
        self.vars["cost_price"] = ctk.StringVar()
        self.vars["selling_price"] = ctk.StringVar()
        self.vars["tax_rate"] = ctk.StringVar()
        self.vars["stock_quantity"] = ctk.StringVar()
        
        InputField(grid_frame, "!JANコード", self.vars["jan"]).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "インストアJAN", self.vars["instore_jan"]).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "仕入先コード", self.vars["id"], readonly=True).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        InputField(grid_frame, "原価", self.vars["cost_price"]).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "売価", self.vars["selling_price"]).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "税率", self.vars["tax_rate"]).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        InputField(grid_frame, "在庫数", self.vars["stock_quantity"]).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # --- 物流・管理 ---
        # 修正: mt引数は存在しないため、padyを使用
        SectionTitle(self.content_frame, title="物流・管理情報").pack(fill="x", pady=(10, 0))
        
        logi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        logi_frame.pack(fill="x")
        logi_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.vars["delivery"] = ctk.StringVar()
        self.vars["delivery_display"] = ctk.StringVar()
        self.vars["shelf"] = ctk.StringVar()
        self.vars["rank"] = ctk.StringVar()
        self.vars["size_w"] = ctk.StringVar()
        self.vars["size_h"] = ctk.StringVar()
        self.vars["size_d"] = ctk.StringVar()
        self.vars["weight"] = ctk.StringVar()

        InputField(logi_frame, "納期", self.vars["delivery"]).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "納期表示", self.vars["delivery_display"]).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "棚番号", self.vars["shelf"]).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        InputField(logi_frame, "品質ランク", self.vars["rank"]).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # サイズ情報 (背景色付きフレーム内)
        size_bg = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray25"))
        size_bg.pack(fill="x", pady=10)
        size_bg.grid_columnconfigure((0,1,2,3), weight=1)
        
        InputField(size_bg, "幅 (mm)", self.vars["size_w"]).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "高さ (mm)", self.vars["size_h"]).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "奥行 (mm)", self.vars["size_d"]).grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        InputField(size_bg, "重量 (g)", self.vars["weight"]).grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # --- 設定・フラグ & メモ (2カラム) ---
        two_col = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        two_col.pack(fill="x", pady=10)
        two_col.grid_columnconfigure((0, 1), weight=1)

        # 左カラム: フラグ
        flag_frame = ctk.CTkFrame(two_col, fg_color="transparent")
        flag_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        SectionTitle(flag_frame, title="設定・フラグ").pack(fill="x")
        
        self.vars["is_published"] = ctk.BooleanVar()
        self.vars["is_sale"] = ctk.BooleanVar()
        self.vars["is_free_shipping"] = ctk.BooleanVar()
        
        CheckBoxField(flag_frame, "公開する", self.vars["is_published"]).pack(anchor="w")
        CheckBoxField(flag_frame, "セール対象", self.vars["is_sale"]).pack(anchor="w")
        CheckBoxField(flag_frame, "送料無料", self.vars["is_free_shipping"]).pack(anchor="w")

        # 右カラム: メモ
        memo_frame = ctk.CTkFrame(two_col, fg_color="transparent")
        memo_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        SectionTitle(memo_frame, title="社内用メモ").pack(fill="x")
        
        self.memo_text = ctk.CTkTextbox(memo_frame, height=80, font=("Meiryo UI", 12))
        self.memo_text.pack(fill="x", pady=5)

        # --- 商品説明エディタ (Split View) ---
        SectionTitle(self.content_frame, title="商品説明 (HTML & プレビュー)").pack(fill="x", pady=(20, 5))
        
        editor_container = ctk.CTkFrame(self.content_frame, border_width=1, border_color=("gray70", "gray40"))
        editor_container.pack(fill="x", pady=5)
        
        # ヘッダー
        editor_header = ctk.CTkFrame(editor_container, height=30, fg_color=("gray95", "gray20"), corner_radius=0)
        editor_header.pack(fill="x")
        ctk.CTkLabel(editor_header, text="商品説明エディタ", font=("Meiryo UI", 11, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(editor_header, text="HTMLソース | プレビュー", font=("Meiryo UI", 10), text_color="gray").pack(side="right", padx=10)

        # Split Body
        split_body = ctk.CTkFrame(editor_container, fg_color="transparent")
        split_body.pack(fill="x")
        split_body.grid_columnconfigure((0, 1), weight=1)
        
        # Left: Source
        self.desc_source = ctk.CTkTextbox(split_body, height=300, font=("Consolas", 12), wrap="none")
        self.desc_source.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.desc_source.bind("<KeyRelease>", self.update_preview)
        
        # Right: Preview (Mock)
        # TkinterにはHTMLレンダリング機能がないため、読み取り専用テキストボックスで代用し、
        # 簡易的にタグを除去したテキストを表示するロジックを入れる
        self.desc_preview = ctk.CTkTextbox(split_body, height=300, font=("Meiryo UI", 13), fg_color=("white", "gray15"), state="disabled")
        self.desc_preview.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def load_active_item(self):
        item = next((i for i in self.data if i["id"] == self.active_id), None)
        if not item: return

        # StringVar/BooleanVar に値をセット
        for key, var in self.vars.items():
            if key in item:
                val = item[key]
                if isinstance(var, ctk.BooleanVar):
                    var.set(bool(val))
                else:
                    var.set(str(val))
        
        # Textbox に値をセット
        self.memo_text.delete("1.0", "end")
        self.memo_text.insert("1.0", item.get("memo", ""))
        
        self.desc_source.delete("1.0", "end")
        self.desc_source.insert("1.0", item.get("description", ""))
        self.update_preview() # プレビュー更新

    def save_current_values(self):
        # 現在のUIの値をデータ配列に書き戻す
        item = next((i for i in self.data if i["id"] == self.active_id), None)
        if not item: return
        
        for key, var in self.vars.items():
            item[key] = var.get()
            
        item["memo"] = self.memo_text.get("1.0", "end-1c")
        item["description"] = self.desc_source.get("1.0", "end-1c")

    def update_preview(self, event=None):
        """HTMLソースから簡易プレビューを生成 (タグ除去)"""
        html_content = self.desc_source.get("1.0", "end-1c")
        
        # 非常に簡易的なHTMLタグ除去（本来はライブラリを使うべき）
        # <br> -> 改行, <li> -> ・, その他タグ -> 削除
        text_content = html_content.replace("<br>", "\n").replace("</p>", "\n\n").replace("</li>", "\n")
        text_content = re.sub(r'<li>', '・ ', text_content)
        text_content = re.sub(r'<[^>]+>', '', text_content)
        
        self.desc_preview.configure(state="normal")
        self.desc_preview.delete("1.0", "end")
        self.desc_preview.insert("1.0", text_content)
        self.desc_preview.configure(state="disabled")


class SettingsView(ctk.CTkScrollableFrame):
    """設定画面"""
    def __init__(self, master, on_back, icons, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_back = on_back
        self.icons = icons
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        back_btn = ctk.CTkButton(header, text="戻る", image=icons.get("back"), width=80, fg_color="transparent", border_width=1, text_color=("gray20", "gray80"), command=on_back)
        back_btn.pack(side="left")
        
        ctk.CTkLabel(header, text="設定", font=("Meiryo UI", 24, "bold")).pack(side="left", padx=20)
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=40, pady=10)
        
        # App Info
        info_card = ctk.CTkFrame(content, corner_radius=15)
        info_card.pack(fill="x", pady=20)
        
        # Gradient bar imitation
        bar = ctk.CTkFrame(info_card, height=5, fg_color=AppColors.ACCENT, corner_radius=5)
        bar.pack(fill="x")
        
        ctk.CTkLabel(info_card, text="eltex CSV Editor", font=("Meiryo UI", 20, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(info_card, text="Version 1.2.0 (Build 20241025)", text_color="gray").pack(pady=(0, 20))
        
        link_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        link_frame.pack(pady=(0, 20))
        ctk.CTkButton(link_frame, text="GitHub Repository", image=icons.get("github"), fg_color=("gray90", "gray30"), text_color=("gray10", "gray90"), hover_color=("gray80", "gray40")).pack(side="left", padx=5)
        ctk.CTkButton(link_frame, text="Website", image=icons.get("web"), fg_color=("gray90", "gray30"), text_color=("gray10", "gray90"), hover_color=("gray80", "gray40")).pack(side="left", padx=5)

        # General Settings
        self.create_settings_section(content, "一般設定", [
            ("テーマ", self.create_theme_selector),
            ("言語", lambda p: ctk.CTkOptionMenu(p, values=["日本語", "English"]).pack(anchor="e")),
            ("自動保存", lambda p: ctk.CTkSwitch(p, text="").pack(anchor="e"))
        ])

        # AI Settings
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
            
            if i < len(items) - 1:
                ctk.CTkFrame(container, height=1, fg_color=("gray90", "gray30")).pack(fill="x")

    def create_theme_selector(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="right")
        
        modes = ["Light", "Dark", "System"]
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        
        def change_theme(mode):
            ctk.set_appearance_mode(mode)
            
        for mode in modes:
            btn = ctk.CTkRadioButton(frame, text=mode, variable=self.theme_var, value=mode, command=lambda m=mode: change_theme(m))
            btn.pack(side="left", padx=5)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("eltex CSV Editor")
        self.geometry("1200x800")
        
        # アイコンの読み込み
        self.icons = self.load_icons()
        
        # データ生成
        self.data = generate_dummy_data()
        
        # レイアウト
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Header
        self.create_header()
        
        # 2. Views (Editor & Settings)
        self.editor_view = EditorView(self, self.data, self.icons)
        self.settings_view = SettingsView(self, self.show_editor, self.icons)
        
        self.show_editor()

    def load_icons(self):
        """
        アイコン画像の読み込み。
        ファイルが存在しない場合はNoneを返し、テキストのみの表示になるようにする。
        """
        icons = {}
        icon_defs = {
            "app": "assets/app_icon.png",
            "save": "assets/save.png",
            "settings": "assets/settings.png",
            "box": "assets/box.png",
            "github": "assets/github.png",
            "web": "assets/globe.png",
            "back": "assets/chevron-left.png"
        }
        
        for name, path in icon_defs.items():
            if os.path.exists(path):
                try:
                    # CTkImageを使うと高解像度対応などが容易
                    pil_image = Image.open(path)
                    icons[name] = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(20, 20))
                except Exception as e:
                    print(f"Error loading icon {path}: {e}")
                    icons[name] = None
            else:
                # ファイルがない場合のプレースホルダー (None)
                # ソースコード上で指定: 'sample.jpg' など外部ファイルが必要な場合はここに配置
                icons[name] = None
        return icons

    def create_header(self):
        header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=(AppColors.HEADER_LIGHT, AppColors.HEADER_DARK))
        header.grid(row=0, column=0, sticky="ew")
        
        # App Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=15, pady=10)
        
        logo_box = ctk.CTkFrame(title_frame, width=30, height=30, fg_color=AppColors.ACCENT, corner_radius=6)
        logo_box.pack(side="left", padx=(0, 10))
        # ここにアプリアイコンがあれば表示
        
        ctk.CTkLabel(title_frame, text="eltex CSV Editor", font=("Meiryo UI", 16, "bold"), text_color="white").pack(side="left")
        
        # Right Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)
        
        self.status_label = ctk.CTkLabel(btn_frame, text=f"読み込み数: {len(self.data)}件", text_color="gray", font=("Meiryo UI", 12))
        self.status_label.pack(side="left", padx=15)
        
        ctk.CTkButton(btn_frame, text="保存", image=self.icons.get("save"), width=100, fg_color="#059669", hover_color="#047857", command=self.on_save).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="", image=self.icons.get("settings"), width=40, fg_color="transparent", hover_color=("gray30", "gray20"), command=self.show_settings).pack(side="left", padx=5)

    def show_editor(self):
        self.settings_view.grid_forget()
        self.editor_view.grid(row=1, column=0, sticky="nsew")

    def show_settings(self):
        self.editor_view.grid_forget()
        self.settings_view.grid(row=1, column=0, sticky="nsew")

    def on_save(self):
        # エディタ側でデータを保存（反映）してからエクスポート処理
        self.editor_view.save_current_values()
        messagebox.showinfo("エクスポート", "CSVファイルとしてエクスポートしました。\n(デモ機能)")

if __name__ == "__main__":
    app = App()
    app.mainloop()