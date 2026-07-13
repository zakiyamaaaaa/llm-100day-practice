import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
client = OpenAI()

class ArticleAnalysis(BaseModel):
    is_positive: bool = Field(description="記事の内容が全体としてポジティブな場合はTrue、ネガティブな場合はFalse")
    sentiment_score: float = Field(description="感情の度合い。0.0（最悪）〜1.0（最高）の範囲の浮動小数点数")
    summary_ja: str = Field(description="記事の要約（日本語で30文字以内）")
    tags: List[str] = Field(description="記事に関連するキーワードのタグ（最大3つまで）")

def main():
    sample_article = """
    某テック企業が開発中だった次世代AIエージェントのリリースを延期すると発表した。
    度重なるバグの発生と、サーバー負荷の予測を見誤ったことが原因とみられている。
    株価は一時的に下落したものの、開発チームは「品質を最優先するための苦渋の決断」とコメントしている。
    """

    print("🤖 記事を分析中...")

    # 🌟 2. OpenAI APIを呼び出す
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なデータアナリストです。与えられた記事を客観的に分析して構造化データを抽出してください。"},
            {"role": "user", "content": sample_article}
        ],
        # ここで先ほど定義したPydanticクラスを指定する
        response_format=ArticleAnalysis,
    )
    
    # 🌟 3. パースされたオブジェクトを直接受け取る
    # response.choices[0].message.parsed には、すでに「ArticleAnalysis」型のオブジェクトが入っています！
    analysis_result: ArticleAnalysis = response.choices[0].message.parsed

    # 4. 結果の確認（文字列ではなく、オブジェクトのプロパティとして型安全にアクセス可能）
    print("\n✅ 分析完了（型安全なデータとして取得成功）\n")
    print(f"ポジティブか？: {analysis_result.is_positive}")
    print(f"感情スコア: {analysis_result.sentiment_score}")
    print(f"日本語要約: {analysis_result.summary_ja}")
    print(f"生成されたタグ: {analysis_result.tags}")

if __name__ == "__main__":
    main()
