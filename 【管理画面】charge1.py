from playwright.sync_api import sync_playwright
import time

LOGIN_URL = "https://www-uat1.fromjapan.dev/japan/adminfj"
USER_ID = "tomii.ryu"
PASSWORD = "hogehoge"
TARGET_UID = "181"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # ==================================================
        # 1. 管理画面ログイン
        # ==================================================
        page.goto(LOGIN_URL)
        page.fill("#username", USER_ID)
        page.fill("#password", PASSWORD)
        page.click("input[type=submit][value='ログイン']")
        page.wait_for_load_state("networkidle")

        # ==================================================
        # 2. 他サイトリスト(進行中)
        # ==================================================
        page.get_by_role("link", name="他サイトリスト(進行中)").click()
        page.wait_for_load_state("networkidle")

        # ==================================================
        # 3. ユーザーID検索
        # ==================================================
        page.fill("input[name='uid']", TARGET_UID)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")

        # ==================================================
        # 4. 一番上の商品を開く
        # ==================================================
        rows = page.locator(
            "table.list_block tbody tr.line1, table.list_block tbody tr.line3"
        )
        print("検索結果件数:", rows.count())

        rows.first.locator("a[href*='/special/edit']").first.click()
        page.wait_for_load_state("networkidle")
        edit_page = page

        # ==================================================
        # 5. 状態を「中古」
        # ==================================================
        edit_page.check("input[name='condition_ex'][value='2']")

        # ==================================================
        # 6. 商品金額 → 振込金額へ反映
        # ==================================================
        item_price = edit_page.locator(
            "input.tm60[readonly]").first.input_value()
        transfer_input = edit_page.locator("input[name='cost']")
        transfer_input.scroll_into_view_if_needed()
        transfer_input.fill(item_price)

        # ==================================================
        # 7. チェック項目ON（JS強制）
        # ==================================================
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

        # ==================================================
        # 8. 注文データを更新
        # ==================================================
        edit_page.evaluate("""
        () => {
          const btn = document.querySelector("input[value='注文データを更新する']");
          if (btn) btn.click();
        }
        """)
        edit_page.wait_for_load_state("networkidle")
        print("✅ 注文データを更新しました")

        # ==================================================
        # 9. 再度一番上の商品を開く
        # ==================================================
        rows = edit_page.locator(
            "table.list_block tbody tr.line1, table.list_block tbody tr.line3"
        )
        rows.first.locator("a[href*='/special/edit']").first.click()
        edit_page.wait_for_load_state("networkidle")

        # ==================================================
        # 10. 「商品を受け取りました」→ パッケージ管理（別タブ）
        # ==================================================
        with context.expect_page() as pinfo:
            edit_page.evaluate("""
            () => {
              const label = document.getElementById("flag_receive_label");
              if (label) label.click();
            }
            """)
        package_page = pinfo.value
        package_page.wait_for_load_state("domcontentloaded")

        # ==================================================
        # 11. 「受取済に更新する」（JS強制）
        # ==================================================
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
        # ==================================================
        # 12. 重量・サイズDOM出現待ち
        # ==================================================
        package_page.wait_for_selector(
            "button[onclick^='return weightSizeAction']",
            timeout=30000
        )

        # ==================================================
        # 13. 重量・サイズ入力（行スコープ完全対応）
        # ==================================================
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
        # ==================================================
        # 14. 重量・サイズ更新（confirm対策）
        # ==================================================
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

        print("🎉 全工程完了")

        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    run()
