# -*- coding: utf-8 -*-
"""给 README 拍一组真实截图。

走的是和 record_demo.py 完全相同的流程与文案（直接 import 那份的 TEXT_*），
只是不录屏、只在关键状态存 PNG。好处是 README 里的图和演示视频里看到的是同一批
界面、同一段输入 —— 视频里说「同源度 94.7%」，README 截图上就是那一屏。

用法：
    LC_DEMO_BASE=https://你的域名 python3 make_screenshots.py

输出到 ../docs/images/。要重拍就删掉旧图重跑，别手改图。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# 复用录屏脚本的文案与交互助手：图、视频、README 三者内容必须一致。
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import record_demo as rd  # noqa: E402

BASE = os.environ.get("LC_DEMO_BASE", "https://logic-coloc-302528-11-1473737765.sh.run.tcloudbase.com")
OUT = HERE.parent / "docs" / "images"
SHOT = {"n": 0}


def shot(page, name: str, full: bool = False) -> None:
    SHOT["n"] += 1
    # 出 JPEG 不出 PNG：这套图是软渐变 + 文字，PNG 一张 500–700KB，七张 4MB，
    # 对仓库太重；JPEG 质量 90 肉眼无差（文字边缘实测清晰），总量降到 ~1.4MB。
    path = OUT / f"{SHOT['n']:02d}-{name}.jpg"
    page.screenshot(path=str(path), full_page=full, type="jpeg", quality=90)
    print(f"  [shot] {path.name}", flush=True)


def wait_pet_quiet(page, timeout_ms: int = 15000) -> None:
    """等看山的庆功浮层收起来再拍。

    候选里出现可靠结论时会触发一次桌宠动作，那是个盖在结果区正中的大浮层，
    帧播完自己消失（restDesktopPet 里置 hidden）。不躲开它，README 里那张
    「同源分析」中间就压着一只举放大镜的猫。
    """
    try:
        page.wait_for_function(
            "() => { const o = document.querySelector('#petReactionOverlay');"
            " return !o || o.hidden; }",
            timeout=timeout_ms,
        )
    except Exception:
        pass


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.jpg"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        ctx = browser.new_context(
            viewport={"width": 430, "height": 932},
            device_scale_factor=2,          # 和成片同一观感：430×932 的 2 倍
            locale="zh-CN",
        )
        page = ctx.new_page()
        rd.page = page                      # record_demo 的助手要用到当前 page

        page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        # CloudBase 测试域名的「风险提醒」闸：点掉再等应用骨架
        if page.title().startswith("风险") and page.locator(".bottom-nav").count() == 0:
            page.wait_for_selector("button:has-text('确定访问')", timeout=20000)
            page.click("button:has-text('确定访问')")
        page.wait_for_selector(".bottom-nav", timeout=45000)
        page.wait_for_timeout(2500)
        shot(page, "home")                  # 求知首页：三个入口

        # ---- 读懂它 ----
        rd.tap(page, 'button.tab[data-panel="explainPanel"]')
        page.wait_for_timeout(900)
        rd.tap(page, '[data-launch-import="manual"]')
        page.wait_for_selector("#manualImportPanel:not([hidden])", timeout=8000)
        rd.type_into(page, "#manualImportText", rd.TEXT_EXPLAIN)
        page.wait_for_timeout(400)
        rd.tap(page, "#confirmManualImport")
        page.wait_for_selector("#explainPanel:not([hidden])", timeout=8000)
        page.wait_for_timeout(800)
        rd.tap(page, "#explainButton")
        rd.wait_llm(page,
                    "document.querySelector('#explainResult') && !document.querySelector('#explainResult').hidden",
                    "#explainError")
        page.wait_for_timeout(1500)
        page.evaluate("document.querySelector('#explainResult').scrollIntoView({behavior:'instant',block:'start'})")
        page.wait_for_timeout(800)
        shot(page, "explain")               # 读懂它：解释正文
        rd.tap(page, "#profileToggle")      # 展开五维逻辑画像
        page.wait_for_timeout(1200)
        page.evaluate("document.querySelector('#profileToggle').scrollIntoView({behavior:'instant',block:'start'})")
        page.wait_for_timeout(600)
        shot(page, "logic-profile")         # 五维逻辑画像

        rd.tap(page, "#backToHome")
        page.wait_for_timeout(1200)

        # ---- 跨学科理解 ----
        rd.tap(page, 'button.tab[data-panel="discoverPanel"]')
        page.wait_for_timeout(900)
        rd.tap(page, '[data-launch-import="manual"]')
        page.wait_for_selector("#manualImportPanel:not([hidden])", timeout=8000)
        rd.type_into(page, "#manualImportText", rd.TEXT_DISCOVER)
        page.wait_for_timeout(400)
        rd.tap(page, "#confirmManualImport")
        page.wait_for_selector("#discoverPanel:not([hidden])", timeout=8000)
        page.wait_for_timeout(800)
        rd.tap(page, "#discoverButton")
        rd.wait_llm(page,
                    "document.querySelector('#discoverResult') && !document.querySelector('#discoverResult').hidden",
                    "#discoverError", timeout_ms=480000)
        page.wait_for_timeout(1500)
        wait_pet_quiet(page)                # 等庆功浮层收掉，别让它压在结果上
        # 对齐 #discoverResult 而不是里面的 #discoverReport：报告正文有时只有两三行，
        # 只滚正文的话这一屏和下一屏的候选卡几乎重合，白占一张图。滚到结果区顶部，
        # 顺带把「底层逻辑相似 ≠ 科学等价」那条原则条一起框进来。
        page.evaluate("document.querySelector('#discoverResult').scrollIntoView({behavior:'instant',block:'start'})")
        page.wait_for_timeout(700)
        shot(page, "discover-report")       # 结果区顶部：原则条 + 跨学科学习报告
        # 候选列表：同源度 + 可靠/受限判定
        page.evaluate("""() => {
          const l = document.querySelector('#candidateList');
          if (l) l.scrollIntoView({behavior:'instant', block:'start'});
        }""")
        page.wait_for_timeout(700)
        shot(page, "discover-candidates")
        # 第一张候选卡的术语对照
        opened = page.evaluate("""() => {
          const btn = [...document.querySelectorAll('#candidateList button')]
            .find(b => b.textContent.includes('术语'));
          if (btn) { btn.click(); return true; }
          return false;
        }""")
        if opened:
            page.wait_for_timeout(1800)
            shot(page, "term-mapping")      # 跨域术语一一映射
            rd.tap(page, "#mappingSheetClose")
            page.wait_for_timeout(600)
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_timeout(500)
        rd.tap(page, "#discoverBackToLauncher")
        page.wait_for_timeout(1000)

        # ---- 知乎搜索 ----
        rd.tap(page, '[data-launch-import="zhihu"]')
        page.wait_for_selector("#zhihuSearchPanel:not([hidden])", timeout=8000)
        rd.type_into(page, "#zhihuSearchQuery", rd.TEXT_ZHIHU, delay=20)
        rd.tap(page, "#confirmZhihuSearch")
        try:
            page.wait_for_function("""() => {
              const list = document.querySelector('#zhihuSearchResults');
              const fb = document.querySelector('#zhihuSearchFeedback');
              const help = document.querySelector('#zhihuSetupHelp');
              if (document.querySelector('#confirmZhihuSearch').disabled) return false;
              return (list && list.children.length > 0) || (help && !help.hidden)
                     || (fb && fb.textContent.includes('失败'));
            }""", timeout=25000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        page.evaluate("""() => {
          const l = document.querySelector('#zhihuSearchResults');
          if (l && l.children.length) l.scrollIntoView({behavior:'instant', block:'start'});
        }""")
        page.wait_for_timeout(700)
        shot(page, "zhihu-search")          # 知乎官方接口搜到的真实讨论
        rd.tap(page, "#importSheetClose")
        page.wait_for_timeout(700)

        browser.close()
    print(f"[done] {SHOT['n']} shots -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
