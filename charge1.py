import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time

def run(playwright: Playwright) -> None:
    # -----------------------------------------------------
    # --- STEP 0: 環境設定とブラウザ起動 ---
    # -----------------------------------------------------
    video_dir = "videos/"
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=video_dir
    )
    page = context.new_page()

    # --- 1. トップページにアクセス ---
    page.goto("https://www-uat1.fromjapan.dev/")

    # --- 2. ログイン操作 ---
    header_login_btn = page.locator("header").get_by_role("button", name="ログイン").first
    expect(header_login_btn).to_be_visible()
    header_login_btn.click()
    page.locator('input[name="login"]').fill("ryuji.tomii@fromjapan.co.jp")
    page.locator('input[name="passwd"]').fill("123qwe")
    page.locator("form").get_by_role("button", name="ログイン").click()

    # --- 3. ログイン成功確認とポップアップ閉鎖 ---
    expect(page.get_by_role("heading", name="マイページ")).to_be_visible(timeout=10000)
    try:
        page.locator('button[aria-label="閉じる"], button:has-text("閉じる")').click(timeout=3000)
    except:
        pass

    # --- 4. Fleamarketタブをクリックし、ページ遷移を待つ ---
    page.locator("#sp-tab").get_by_text("JDirectItems Fleamarket").click()
    page.wait_for_load_state("networkidle")

    # --- 5. 左上の商品をクリック（別タブで開く） ---
    with context.expect_page() as new_page_info:
        # ロケーターを信頼性の高いものに修正（以前のデバッグ結果を反映）
        page.locator(".item-box").first.click(timeout=60000)

    # --- 6. 新しいページ（商品詳細ページ）で操作を継続 ---
    detail_page = new_page_info.value
    detail_page.wait_for_load_state("networkidle")

    # --- 7. カートに入れる ---
    # 厳密なロケーターとスクロール処理で安定化
    cart_button_locator = detail_page.locator("button.fj-button-extra-large.fj-button-primary-filled:has-text(\"カートに入れる\"):visible").first
    
    # クリック可能にするためにスクロール（非表示要素対策）
    cart_button_locator.scroll_into_view_if_needed(timeout=10000)

    # クリック実行
    cart_button_locator.click(timeout=30000) 
    
    # カート投入後の処理が安定するまで待機
    detail_page.wait_for_load_state("networkidle")

    # --- 8. レジに進む（カート画面から請求1画面へ） --
    # クリック可能にするためにスクロール
    checkout_button_locator = detail_page.get_by_role("button", name="レジに進む").first
    checkout_button_locator.scroll_into_view_if_needed(timeout=10000)

    # レジボタンを強制クリック (Timeout 60秒)
    checkout_button_locator.click(force=True, timeout=60000)
    
    # -----------------------------------------------------
    # --- STEP 9: 請求画面での操作 ---
    # -----------------------------------------------------

    # ページ遷移待ち
    # ページ遷移待ち (レジ画面への遷移後)
    detail_page.wait_for_load_state("networkidle")

    # --- 9. FJポイントの適用ボタンを押す (全ポイント利用) ---
    
    # 1. 利用可能ポイントのテキストから数値部分を抽出
    available_points_locator = detail_page.locator("span.text-lg.font-semibold:has-text('FJポイント(利用可能')")
    points_text = available_points_locator.inner_text(timeout=10000)
    match = re.search(r"(\d{1,3}(,\d{3})*)", points_text)
    
    # 【重要】変数の定義を確定
    if match:
        available_points = match.group(0).replace(",", "")
    else:
        # 抽出できなかった場合のフォールバック
        available_points = "9999999" 
        
    # 2. 【修正】入力フィールドの特定と値の入力（ロケーターを修正）
    #    「利用するFJポイント」の親要素まで遡り、その中にある input を探す
    detail_page.get_by_text("利用するFJポイント").locator("xpath=../..").locator("input.vs-inputx").fill(available_points, timeout=60000)
    # ロケーター：get_by_text("利用するFJポイント") -> 親要素(..) -> その中のinput[type="text"]
    
    # 3. FJポイントのセクション全体を特定し、スクロール
    points_section = detail_page.get_by_text("利用するFJポイント").locator("xpath=../../..")

    # 4. そのセクション内の「適用」ボタンをクリック (Timeout 60秒)
    points_section.get_by_role("button", name="適用").click(timeout=60000)
    
    # 適用後のページの安定化を待つ
    detail_page.wait_for_load_state("networkidle")

    # --- 10. 注文確定ボタン ---
    order_btn = detail_page.get_by_role("button", name="利用規約に同意して 注文確定")
    order_btn.scroll_into_view_if_needed(timeout=10000) 
    order_btn.click(timeout=15000)

    # 注文後の確認ボタン（あれば）
    try:
        confirm_btn = detail_page.get_by_role("button", name="確認")
        confirm_btn.click(timeout=10000)
    except:
        pass

    # --- 10. 完了画面へ ---
    detail_page.goto("https://www-uat1.fromjapan.dev/japan/charge/special/finish")
    print("処理完了!")

    # --- 11. ブラウザ閉じる ---
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)