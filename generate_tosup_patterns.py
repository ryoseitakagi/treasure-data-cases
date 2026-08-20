"""Generate customer-signal routing patterns for the sales-assist chatbot.

The six seed rows mirror the attached checklist. `generated_patterns` contains
1,000 additional, distinct customer-utterance variants so the matcher can
recognize the underlying business situation rather than one exact sentence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "tosup_patterns.json"

SEEDS = [
    {
        "id": "pdf-001",
        "source": "attached-checklist",
        "utterance": "SnowflakeやBigQueryはあるがマーケ活用が不安",
        "usecase": "composable_cdp",
        "label": "Composable CDPの拡張",
        "products": ["cdp", "audience"],
    },
    {
        "id": "pdf-002",
        "source": "attached-checklist",
        "utterance": "MAのシナリオ作成や施策運用をAIで自動化したい",
        "usecase": "ai_ma",
        "label": "AI + MA｜TAS + Engage Studio",
        "products": ["engage", "journey", "ai_agent"],
    },
    {
        "id": "pdf-003",
        "source": "attached-checklist",
        "utterance": "DWHの維持費が高い／クラウド刷新・移行を検討中",
        "usecase": "dwh_migration",
        "label": "DWH Migration Defense",
        "products": ["cdp"],
    },
    {
        "id": "pdf-004",
        "source": "attached-checklist",
        "utterance": "商談の会話や音声データを分析・活用したい",
        "usecase": "ai_voice",
        "label": "AI Voiceの活用",
        "products": ["ai_voice"],
    },
    {
        "id": "pdf-005",
        "source": "attached-checklist",
        "utterance": "広告費用対効果が落ちている／運用をデジタル化したい",
        "usecase": "paid_media",
        "label": "Digital Worker｜Paid Media代替",
        "products": ["audience", "ai_agent"],
    },
    {
        "id": "pdf-006",
        "source": "attached-checklist",
        "utterance": "社内データをAIが探索・分析できるように基盤化したい",
        "usecase": "ai_explorable",
        "label": "Treasure AI Studio｜AI-Explorable基盤",
        "products": ["ai_agent", "cdp"],
    },
]

PREFIXES = [
    "「{core}」と顧客が話していた",
    "商談で顧客から「{core}」という発言があった",
    "顧客担当者に「{core}」と相談された",
    "顧客の一言が「{core}」だった",
    "顧客から「{core}」という悩みを聞いた",
]

CONFIGS = [
    {
        "usecase": "composable_cdp", "label": "Composable CDPの拡張", "target": 170,
        "products": ["cdp", "audience"],
        "keywords": ["DWH", "データ統合", "マーケティング活用", "セグメント", "1st Partyデータ"],
        "cores": [
            "既存DWHの顧客データをマーケ施策に直接つなげたい",
            "Snowflakeにある顧客情報を配信リストへ活用したい",
            "BigQueryの購買データをキャンペーンの条件に使いたい",
            "分析基盤とマーケティング施策の間にある分断をなくしたい",
            "データを別環境へ大量コピーせずに顧客を抽出したい",
            "マーケターがSQLを書かずに既存データからセグメントを作りたい",
            "DWHに蓄積した行動履歴を広告やCRMへつなげたい",
            "顧客IDを軸に複数のデータソースを施策で使えるようにしたい",
            "社内のデータ基盤を活かしたままCDPの機能を広げたい",
            "マーケ部門がデータ基盤へ安全にアクセスできるようにしたい",
            "データの持ち出しを増やさずパーソナライズ配信を始めたい",
            "店舗とECの顧客データを統合して施策に使いたい",
            "BtoBの営業データとマーケデータを一つの顧客単位で見たい",
            "複数ブランドのDWHを横断して顧客セグメントを作りたい",
            "データレイクの情報をマーケティング担当者が使える形にしたい",
            "既存のクラウドデータ基盤に施策実行の出口を追加したい",
            "顧客データをコピーする運用のコストとリスクを抑えたい",
            "データウェアハウスの価値を分析以外の施策にも広げたい",
        ],
        "contexts": [
            "マーケターが自分で使える形にしたい", "複製データを増やしたくない",
            "個人情報の管理範囲を広げずに進めたい", "既存投資を無駄にしたくない",
            "広告・メール・アプリを横断して活用したい", "データガバナンスを保ったまま実行したい",
            "部門ごとのデータを顧客単位でまとめたい", "施策のたびにデータ部門へ依頼したくない",
            "小さく始めて対象チャネルを広げたい", "現行のDWH構成を変えずに試したい",
        ],
    },
    {
        "usecase": "ai_ma", "label": "AI + MA｜TAS + Engage Studio", "target": 170,
        "products": ["engage", "journey", "ai_agent"],
        "keywords": ["MA", "AI", "シナリオ", "配信", "顧客行動予測"],
        "cores": [
            "顧客行動に応じたMAシナリオを毎回手作業で設計している",
            "キャンペーンの分岐条件をAIに考えてほしい",
            "メールやLINEの配信内容を顧客ごとに自動で変えたい",
            "施策のターゲット抽出と配信設定に時間がかかっている",
            "MAのシナリオが増えすぎて全体を管理できない",
            "顧客の次の行動を予測して最適な接点を選びたい",
            "施策担当者が毎回同じ配信設定を作り直している",
            "休眠しそうな顧客へのコミュニケーションを自動化したい",
            "反応率に応じて配信内容を自動で改善したい",
            "メール文面の作成とセグメント設計を効率化したい",
            "複数チャネルのジャーニーをAIで組み立てたい",
            "マーケティング施策のPDCAをもっと短いサイクルで回したい",
            "配信タイミングを顧客ごとに最適化したい",
            "担当者の経験に依存しているMA運用を標準化したい",
            "一斉配信から顧客行動ベースの施策へ変えたい",
            "施策の優先順位をAIに提案してほしい",
            "キャンペーン終了後の分析から次の施策まで自動化したい",
            "現場がノーコードで複雑な顧客シナリオを動かしたい",
        ],
        "contexts": [
            "人手を増やさず配信本数を増やしたい", "担当者によるばらつきを減らしたい",
            "メールとLINEとアプリをつなげたい", "顧客体験を崩さずに自動化したい",
            "施策の準備時間を短縮したい", "少人数のマーケチームで運用したい",
            "購買や閲覧の変化にすぐ反応したい", "配信対象の重複や漏れをなくしたい",
            "経営層にも施策効果を説明しやすくしたい", "既存MAを活かして高度化したい",
        ],
    },
    {
        "usecase": "dwh_migration", "label": "DWH Migration Defense", "target": 160,
        "products": ["cdp"],
        "keywords": ["DWH", "移行", "コスト削減", "パフォーマンス", "クラウド刷新"],
        "cores": [
            "DWHの利用料が毎月増え続けていて見直したい",
            "クエリが遅くなりマーケティング分析に時間がかかる",
            "クラウドDWHの刷新や移行を検討している",
            "データ量の増加にインフラ費用が追いつかない",
            "同時実行が増えてDWHの処理性能が限界に近い",
            "古いデータ基盤を新しいクラウドへ移したい",
            "DWHのコスト最適化を経営から求められている",
            "データ処理の遅延で施策の開始が後ろ倒しになっている",
            "分析用と施策用のワークロードを分けたい",
            "クラウド移行の前に現状のデータ処理を診断したい",
            "データ基盤の運用費とライセンス費を下げたい",
            "大規模ログを処理するたびに計算資源が膨らむ",
            "DWHの性能問題で利用部門から不満が出ている",
            "新しいデータ基盤への移行リスクを抑えたい",
            "インフラ刷新の投資対効果を説明できる材料がほしい",
            "データ基盤の統合で運用をシンプルにしたい",
            "クラウドの従量課金が予算を圧迫している",
            "分析基盤を維持しながら処理コストを下げたい",
        ],
        "contexts": [
            "既存のデータ資産を失わずに進めたい", "移行期間中も業務を止めたくない",
            "性能とコストを同時に改善したい", "経営会議に具体的な削減案を出したい",
            "大規模データを安定して扱いたい", "現場のクエリを大きく変えたくない",
            "マルチクラウドの選択肢を比較したい", "運用チームの負荷も減らしたい",
            "段階的に移行して失敗を避けたい", "将来のデータ増加にも備えたい",
        ],
    },
    {
        "usecase": "ai_voice", "label": "AI Voiceの活用", "target": 170,
        "products": ["ai_voice"],
        "keywords": ["音声", "会話分析", "コンタクトセンター", "商談", "VOC"],
        "cores": [
            "商談の録音を分析して顧客のニーズを把握したい",
            "コールセンターの会話ログを施策に活かせていない",
            "音声データをテキスト化するだけで終わらせたくない",
            "営業トークの中から失注理由や要望を見つけたい",
            "顧客の声を人手で聞き直す作業を減らしたい",
            "問い合わせの会話から商品改善のヒントを抽出したい",
            "通話内容を分析して営業担当者の育成に使いたい",
            "カスタマーサポートの応対品質を定量化したい",
            "VOCを部門横断で集めて経営判断につなげたい",
            "音声に埋もれている顧客の不満を早く検知したい",
            "電話対応の内容から解約リスクを把握したい",
            "商談メモを自動化して営業の入力負荷を減らしたい",
            "会話の中のキーワードをリアルタイムに検知したい",
            "カスハラの兆候を通話データから見つけたい",
            "電話とメールに分散した顧客の声を統合したい",
            "担当者ごとの応対差を会話データで確認したい",
            "面談や会議の音声をナレッジとして再利用したい",
            "非構造化の会話データをマーケティングに取り込みたい",
        ],
        "contexts": [
            "録音はあるが聞き返す人手が足りない", "現場の声を経営に届けたい",
            "顧客の本音を定性的なままにしたくない", "品質管理を担当者の抜き打ち確認に頼りたくない",
            "営業力の底上げにつなげたい", "カスタマーハラスメントにも備えたい",
            "会話データを安全に扱いたい", "応対記録の入力時間を短くしたい",
            "VOCから新しい施策を見つけたい", "音声と顧客属性を組み合わせたい",
        ],
    },
    {
        "usecase": "paid_media", "label": "Digital Worker｜Paid Media代替", "target": 160,
        "products": ["audience", "ai_agent"],
        "keywords": ["広告", "ROAS", "CPA", "Paid Media", "1st Partyデータ"],
        "cores": [
            "広告運用の費用対効果が以前より下がっている",
            "広告予算を増やさずにコンバージョンを伸ばしたい",
            "1st Partyデータを広告配信の精度向上に使いたい",
            "広告オーディエンスの作成を毎回手作業で行っている",
            "リターゲティングに頼らず新規顧客を獲得したい",
            "媒体ごとの広告データと自社顧客データをつなぎたい",
            "キャンペーンの入稿や予算配分を自動化したい",
            "ROASの良い顧客セグメントを見つけて配信したい",
            "Cookieに依存しない広告施策へ移行したい",
            "広告代理店に任せきりの運用を見直したい",
            "広告クリック後の顧客行動まで評価したい",
            "新規と既存の顧客を分けて広告を最適化したい",
            "クリエイティブごとの成果を顧客属性と結び付けたい",
            "CPAが悪化した原因をデータから特定したい",
            "広告配信の除外リストを最新状態に保ちたい",
            "オフラインの購買情報を広告改善に生かしたい",
            "運用担当者の判断に依存した広告最適化を変えたい",
            "広告施策の検証サイクルをもっと短くしたい",
        ],
        "contexts": [
            "媒体ごとにデータが分かれている", "広告費が無駄打ちになっている感覚がある",
            "新規獲得とLTVを一緒に見たい", "施策の実行量を増やしたい",
            "マーケ担当者の作業を減らしたい", "プライバシーに配慮して活用したい",
            "予算配分をデータで説明したい", "広告とCRMの連携を強めたい",
            "アッパーファネルも改善したい", "運用を自動化して戦略に時間を使いたい",
        ],
    },
    {
        "usecase": "ai_explorable", "label": "Treasure AI Studio｜AI-Explorable基盤", "target": 170,
        "products": ["ai_agent", "cdp"],
        "keywords": ["社内データ", "AI探索", "自然言語", "分析基盤", "データ活用"],
        "cores": [
            "社内のデータをAIに質問して答えを得られるようにしたい",
            "データ分析のたびに専門チームへ依頼する状況を変えたい",
            "生成AIが社内データを安全に参照できる基盤を作りたい",
            "データカタログを整備して探せる状態にしたい",
            "自然言語で売上や顧客の状況を分析したい",
            "現場部門が自分でデータから仮説を作れるようにしたい",
            "社内ナレッジと顧客データをAIで横断して使いたい",
            "AIに見せてよいデータを制御しながら活用したい",
            "分析モデルが参照するデータ基盤を整えたい",
            "データの意味や定義をAIが理解できるようにしたい",
            "レポート作成のための集計作業を減らしたい",
            "経営層がすぐにデータへ質問できる環境がほしい",
            "データ活用を一部のアナリストだけの仕事にしたくない",
            "複数部門のデータをAIで横断的に調べたい",
            "AIによる分析の回答に根拠を付けたい",
            "社内データを活用したアプリやエージェントを作りたい",
            "データアクセスの申請待ちで意思決定が遅れている",
            "分析できる人材不足をAIで補いたい",
        ],
        "contexts": [
            "権限管理と監査を前提にしたい", "回答の根拠を追跡できるようにしたい",
            "現場のデータリテラシーを底上げしたい", "既存のデータ基盤を活かしたい",
            "部門をまたいだ意思決定を速くしたい", "機密情報を安全に扱いたい",
            "AIの回答を業務フローに組み込みたい", "データの定義揺れを減らしたい",
            "分析依頼の backlog を減らしたい", "小さな部門から段階的に始めたい",
        ],
    },
]


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def make_keywords(config: dict, core: str, context: str) -> list[str]:
    values = list(config["keywords"])
    for value in re.split(r"[、。／/・「」『』\s]+", core + " " + context):
        if len(value) >= 2 and value not in values:
            values.append(value)
    return values[:18]


def main() -> None:
    generated: list[dict] = []
    seen: set[str] = set()
    pdf_phrases = {normalize(item["utterance"]) for item in SEEDS}
    for config in CONFIGS:
        for core in config["cores"]:
            for context in config["contexts"]:
                for prefix in PREFIXES:
                    utterance = prefix.format(core=f"{core}。{context}")
                    key = normalize(utterance)
                    if key in seen or key in pdf_phrases:
                        continue
                    seen.add(key)
                    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
                    generated.append({
                        "id": f"gen-{len(generated) + 1:04d}-{digest}",
                        "source": "generated-customer-signal",
                        "utterance": utterance,
                        "usecase": config["usecase"],
                        "label": config["label"],
                        "products": config["products"],
                        "keywords": make_keywords(config, core, context),
                        "handoff_reason": f"{config['label']}の相談シグナル。顧客の発言を起点に、現状のデータ・運用・成果指標を確認する。",
                    })
                    if len([x for x in generated if x["usecase"] == config["usecase"]]) >= config["target"]:
                        break
                if len([x for x in generated if x["usecase"] == config["usecase"]]) >= config["target"]:
                    break
            if len([x for x in generated if x["usecase"] == config["usecase"]]) >= config["target"]:
                break
    if len(generated) != 1000:
        raise RuntimeError(f"Expected exactly 1000 generated patterns, got {len(generated)}")
    payload = {
        "version": 1,
        "description": "顧客の自然な発言からユースケースを推定するトスアップパターン",
        "seed_patterns": SEEDS,
        "generated_count": len(generated),
        "generated_patterns": generated,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for item in generated:
        counts[item["usecase"]] = counts.get(item["usecase"], 0) + 1
    print("generated", len(generated), "patterns", counts)


if __name__ == "__main__":
    main()
