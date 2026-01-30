from playwright.sync_api import sync_playwright
LOGIN_URL = "https://www-uat1.fromjapan.dev/jp/member/login/"
USER_ID = "ryuji.tomii@fromjapan.co.jp"
PASSWORD = "123qwe"
TARGET_UID = "181"


def test_shipping_designation():
    """倉庫到着商品の配送先指定のE2Eテスト"""
    print("テスト開始")
    with sync_playwright() as p:

        # 1. ブラウザの起動
        print("Playwright起動")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print("ブラウザ起動完了")

        try:
            # 2. ログインページにアクセス
            print("ログインページにアクセス中...")
            page.goto(LOGIN_URL)
            page.wait_for_load_state("networkidle")

            # 3. メールアドレスを入力
            page.locator('input[name="login"]').fill(USER_ID)

            # 4. パスワードを入力
            page.locator('input[name="passwd"]').fill(PASSWORD)

            # 5. ログインボタンを押下
            page.locator("form").get_by_role("button", name="ログイン").click()

            # 6. ログイン完了を待機
            page.wait_for_load_state("networkidle")

            # 7. ヘッダーメニューから「配送指定」を押下
            page.locator(
                'svg.feather-package').wait_for(state="visible", timeout=10000)
            page.click('a:has(svg.feather-package)')

            # 8. 配送指定ページの読み込みを待機
            page.wait_for_load_state("networkidle")

            # 9. 商品選択エリアで一番上の商品のチェックボックスをON
            page.locator('label.fj-checkbox').nth(1).click(force=True)

            # 10. 「次へ」ボタンを押下
            page.click('.fj-button-large.h-full.fj-button-primary-filled')

            # 11. 発送方法ページの読み込みを待機
            page.wait_for_load_state("networkidle")

            # 12. 一番上の配送業者のラジオボタンをON
            page.locator(
                'label.vs-component.con-vs-radio.vs-radio-ship-select').first.click()

            # 13. お支払い方法で「クレジットカード」のラジオボタンをON
            credit_card_label = page.locator(
                'span.vs-radio--label:has-text("クレジットカード")').first
            credit_card_label.click()

            # 14. 「利用するFJポイント」の「適用」ボタンを押下
            page.get_by_role('button', name='適用').nth(1).click()

            # 15. 「次へ」ボタンを押下
            page.get_by_role('button', name='次へ').last.click()

            # 16. 確認ページの読み込みを待機
            page.wait_for_load_state("networkidle")

            # 17. 「利用規約に同意して確定」ボタンを押下
            confirm_button = page.locator(
                'button[type="submit"].fj-button-primary-filled.fj-button-large:has-text("確定")').first
            confirm_button.click()

            # 18. 完了ページの表示を確認
            page.wait_for_load_state("networkidle")

            # 19. テスト結果の検証
            success_message = page.locator('text=完了').first
            assert success_message.is_visible(), "完了メッセージが表示されていません"

            print("✓ テスト成功: 配送先指定が完了しました")

        finally:
            # 20. ブラウザのクリーンアップ
            browser.close()


if __name__ == "__main__":
    test_shipping_designation()
