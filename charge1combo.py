import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time

# 管理画面の設定
ADMIN_LOGIN_URL = "https://www-uat1.fromjapan.dev/japan/adminfj"
ADMIN_USER_ID = "tomii.ryu"
ADMIN_PASSWORD = "hogehoge"
TARGET_UID = "181"

# フロント側の設定
FRONT_USER_EMAIL = "ryuji.tomii@fromjapan.co.jp"
FRONT_USER_PASSWORD = "123qwe"


def front_process(context) -> None:
    """フロント側での処理（請求1決済）- 商品購入"""
    print("=" * 50)
    print("フロント側での処理を開始（商品購入）")
    print("=" * 50)

    page = context.new_page()

    # 1. トップページにアクセス
    page.goto("https://www-uat1.fromjapan.dev/")

    # 2. ログイン操作
    header_login_btn = page.locator(
        "header").get_by_role("button", name="ログイン").first
    expect(header_login_btn).to_be_visible()
    header_login_btn.click()
    page.locator('input[name="login"]').fill(FRONT_USER_EMAIL)
    page.locator('input[name="passwd"]').fill(FRONT_USER_PASSWORD)
    page.locator("form").get_by_role("button", name="ログイン").click()

    # 3. ログイン成功確認とポップアップ閉鎖
    expect(page.get_by_role("heading", name="マイページ")
           ).to_be_visible(timeout=10000)
    try:
        page.locator(
            'button[aria-label="閉じる"], button:has-text("閉じる")').click(timeout=3000)
    except:
        pass

    # 4. Fleamarketタブをクリックし、ページ遷移を待つ
    page.locator("#sp-tab").get_by_text("JDirectItems Fleamarket").click()
    page.wait_for_load_state("networkidle")

    # 5. 左上の商品をクリック（別タブで開く）
    with context.expect_page() as new_page_info:
        page.locator(".item-box").first.click(timeout=60000)

    # 6. 新しいページ（商品詳細ページ）で操作を継続
    detail_page = new_page_info.value
    detail_page.wait_for_load_state("networkidle")

    # 7. カートに入れる
    cart_button_locator = detail_page.locator(
        "button.fj-button-extra-large.fj-button-primary-filled:has-text(\"カートに入れる\"):visible").first
    cart_button_locator.scroll_into_view_if_needed(timeout=10000)
    cart_button_locator.click(timeout=30000)
    detail_page.wait_for_load_state("networkidle")

    # 8. レジに進む（カート画面から請求1画面へ）
    checkout_button_locator = detail_page.get_by_role(
        "button", name="レジに進む").first
    checkout_button_locator.scroll_into_view_if_needed(timeout=10000)
    checkout_button_locator.click(force=True, timeout=60000)
    detail_page.wait_for_load_state("networkidle")

    # 9. FJポイントの適用ボタンを押す (全ポイント利用)
    available_points_locator = detail_page.locator(
        "span.text-lg.font-semibold:has-text('FJポイント(利用可能')")
    points_text = available_points_locator.inner_text(timeout=10000)
    match = re.search(r"(\d{1,3}(,\d{3})*)", points_text)

    if match:
        available_points = match.group(0).replace(",", "")
    else:
        available_points = "9999999"

    detail_page.get_by_text("利用するFJポイント").locator(
        "xpath=../..").locator("input.vs-inputx").fill(available_points, timeout=60000)

    points_section = detail_page.get_by_text(
        "利用するFJポイント").locator("xpath=../../..")
    points_section.get_by_role("button", name="適用").click(timeout=60000)
    detail_page.wait_for_load_state("networkidle")

    # 10. 注文確定ボタン
    order_btn = detail_page.get_by_role("button", name="利用規約に同意して 注文確定")
    order_btn.scroll_into_view_if_needed(timeout=10000)
    order_btn.click(timeout=15000)

    try:
        confirm_btn = detail_page.get_by_role("button", name="確認")
        confirm_btn.click(timeout=10000)
    except:
        pass

    # 11. 完了画面へ
    detail_page.goto(
        "https://www-uat1.fromjapan.dev/japan/charge/special/finish")
    print("✅ フロント側での処理が完了しました（商品購入完了）")

    # ページは閉じない（ブラウザを維持するため）
    # page.close()
    # detail_page.close()


def admin_process(context) -> None:
    """管理画面での処理"""
    print("=" * 50)
    print("管理画面での処理を開始")
    print("=" * 50)

    page = context.new_page()

    # 1. 管理画面ログイン
    page.goto(ADMIN_LOGIN_URL)
    page.fill("#username", ADMIN_USER_ID)
    page.fill("#password", ADMIN_PASSWORD)
    page.click("input[type=submit][value='ログイン']")
    page.wait_for_load_state("networkidle")

    # 2. 他サイトリスト(進行中)
    page.get_by_role("link", name="他サイトリスト(進行中)").click()
    page.wait_for_load_state("networkidle")

    # 3. ユーザーID検索
    page.fill("input[name='uid']", TARGET_UID)
    page.click("input[type='submit']")
    page.wait_for_load_state("networkidle")

    # 4. 一番上の商品を開く
    rows = page.locator(
        "table.list_block tbody tr.line1, table.list_block tbody tr.line3"
    )
    print("検索結果件数:", rows.count())

    rows.first.locator("a[href*='/special/edit']").first.click()
    page.wait_for_load_state("networkidle")
    edit_page = page

    # 5. 状態を「中古」
    edit_page.check("input[name='condition_ex'][value='2']")

    # 6. 商品金額 → 振込金額へ反映
    item_price = edit_page.locator("input.tm60[readonly]").first.input_value()
    transfer_input = edit_page.locator("input[name='cost']")
    transfer_input.scroll_into_view_if_needed()
    transfer_input.fill(item_price)

    # 7. チェック項目ON（JS強制）
    edit_page.evaluate("""
    () => {
      const labels = [
        "注文しました",
        "代金を支払いました",
        "ストア／出品者からの発送を確認しました"
      ];
      labels.forEach(text => {
        const label = [...document.querySelectorAll("label")]
          .find(l => l.textContent.includes(text));
        if (label) label.click();
      });
    }
    """)

    # 8. 注文データを更新
    edit_page.evaluate("""
    () => {
      const btn = document.querySelector("input[value='注文データを更新する']");
      if (btn) btn.click();
    }
    """)
    edit_page.wait_for_load_state("networkidle")
    print("✅ 注文データを更新しました")

    # 9. 再度一番上の商品を開く
    rows = edit_page.locator(
        "table.list_block tbody tr.line1, table.list_block tbody tr.line3"
    )
    rows.first.locator("a[href*='/special/edit']").first.click()
    edit_page.wait_for_load_state("networkidle")

    # 10. 「商品を受け取りました」→ パッケージ管理（別タブ）
    with context.expect_page() as pinfo:
        edit_page.evaluate("""
        () => {
          const label = document.getElementById("flag_receive_label");
          if (label) label.click();
        }
        """)
    package_page = pinfo.value
    package_page.wait_for_load_state("domcontentloaded")

    # 11. 「受取済に更新する」（JS強制）
    package_page.wait_for_selector(
        "input[type='submit'][value='受取済に更新する']",
        timeout=30000
    )

    package_page.evaluate("""
    () => {
     const btn = document.querySelector(
       "input[type='submit'][value='受取済に更新する']"
      );
      if (!btn) throw new Error("受取済に更新するボタンが見つかりません");
      btn.click();
    }
    """)

    # 12. 重量・サイズDOM出現待ち
    package_page.wait_for_selector(
        "button[onclick^='return weightSizeAction']",
        timeout=30000
    )

    # 13. 重量・サイズ入力（行スコープ完全対応）
    package_page.evaluate("""
    () => {
      const ws = document.querySelector('.packs .pack .ws');
      if (!ws) throw new Error('ws not found');

      const set = (selector, value) => {
        const el = ws.querySelector(selector);
        if (!el) throw new Error('要素が見つかりません: ' + selector);
        el.value = value;
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur',   { bubbles: true }));
      };

      set('input.weight', '1');
      set('input[name^="length"]', '1');
      set('input[name^="width"]',  '1');
      set('input[name^="height"]', '1');
    }
    """)

    # 14. 重量・サイズ更新（confirm対策）
    package_page.wait_for_selector(
        "button[onclick^='return weightSizeAction']",
        timeout=30000
    )

    package_page.evaluate("""
    () => {
     window.confirm = () => true;
     const btn = document.querySelector(
     "button[onclick^='return weightSizeAction']"
    );
     if (!btn) throw new Error("重量・サイズ更新ボタンが見つかりません");
     btn.click();
    }
    """)

    print("✅ 管理画面での処理が完了しました")

    # 管理画面のページも閉じない（最後にまとめて閉じる）
    # page.close()


def run(playwright: Playwright) -> None:
    """メイン処理：フロント側（商品購入） → 管理画面を同一ブラウザで実行"""
    print("\n" + "=" * 50)
    print("請求1決済の自動化処理を開始します")
    print("=" * 50 + "\n")

    # ブラウザを1回だけ起動
    video_dir = "videos/"
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=video_dir
    )

    try:
        # Step 1: フロント側での処理（商品購入）
        front_process(context)

        print("\n" + "=" * 50)
        print("商品購入完了、管理画面での処理を開始します")
        print("=" * 50 + "\n")

        # 少し待機してから次の処理へ（データベース反映待ち）
        print("データベース反映を待機中...")
        time.sleep(5)

        # Step 2: 管理画面での処理
        admin_process(context)

        print("\n" + "=" * 50)
        print("🎉 全ての処理が完了しました！")
        print("=" * 50 + "\n")

        # 処理完了後、少し待機してからブラウザを閉じる
        time.sleep(3)

    finally:
        # 最後にまとめてブラウザを閉じる
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
