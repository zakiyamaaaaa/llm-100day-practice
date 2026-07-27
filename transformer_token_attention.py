import math

# 1. Tokenizerの簡易版
def tokenize(text: str) -> list[str]:
    """
    文章をTokenに分割する。

    これは学習用の簡易Tokenizer。
    実際のLLMは、より複雑なTokenizerを使用する。
    """
    
    return text.split()

# 1. TokenをToken IDに変換する
def build_token_ids(tokens: list[str])->dict[str, int]:
    """
    Tokenと整数IDの対応表を作る。

    LLM内部では、Tokenをそのまま扱わず、
    整数のIDに変換して処理する。
    """
    
    return {
        token: index
        for index, token in enumerate(tokens)
    }

# ベクトル計算用の関数
def dot_product(left: list[float], right: list[float]) -> float:
    """
    2つのベクトルの内積を計算する。

    Attentionでは、QueryとKeyの近さを
    内積によって計算する。
    """
    
    return sum( left_value * right_value for left_value, right_value in zip(left, right))

def softmax(values: list[float]) -> list[float]:
    """
    数値を確率のような値に変換する。

    出力された値の合計は1になる。
    値が大きい要素ほど、大きな重みになる。
    """
    
    # 数値が大きすぎたときのoverflowを防ぐ
    max_value = max(values)
    
    exponentials = [math.exp(value - max_value) for value in values]
    
    total = sum(exponentials)
    
    return [ value /total for value in exponentials]

def weighted_sum(weights: list[float], values: list[list[float]]) -> list[float]:
    """
    Attentionの重みを使ってValueを合成する。

    重みが大きいValueほど、出力に強く反映される。
    """
    
    dimension = len(values[0])
    
    result = [0.0]*dimension
    
    for weight, value in zip(weights, values):
        for index in range(dimension):
            result[index] += weight*value[index]
            
    return result

# 4. Scaled Dot-Product Attention
def scaled_dot_product_attention(query: list[float],
    keys: list[list[float]],
    values: list[list[float]],
) -> tuple[list[float], list[float], list[float]]:
    """
    1つのQueryが、複数のKeyとValueを参照する。

    処理の流れ:

    1. Queryと各Keyの内積を計算
    2. sqrt(dimension)で割る
    3. softmaxでAttention重みに変換
    4. 重み付きでValueを合成
    """
    
    dimension = len(query)
    
    # Queryと各keyの関連度を計算する
    raw_scores = [dot_product(query, key) for key in keys]
    
    # スコアが大きくならないように調整
    scale = math.sqrt(dimension)
    scaled_scores = [score/scale for score in raw_scores]
    
    # 各keyをどの程度参照するかを確立に変換する
    attention_weights = softmax(scaled_scores)
    
    # Attentionの重みでValueを合成する
    output = weighted_sum(weights=attention_weights, values=values)
    return (raw_scores, attention_weights, output)

# 5. Context Windowを確認する
def check_context_window(tokens: list[str], max_tokens: int,) -> None:
    """
    Token数がContext Windowの上限以内か確認する。
    """

    token_count = len(tokens)

    print()
    print("=" * 60)
    print("Context Windowの確認")
    print("=" * 60)
    print(f"Token数: {token_count}")
    print(f"上限: {max_tokens}")

    if token_count <= max_tokens:
        print("結果: Context Window内に収まっています")
    else:
        print("結果: Context Windowを超えています")
        
# 6. TokenとEmbeddingのデモ
def run_token_demo() -> None:
    """Token、Token ID、Embeddingの関係を表示する。"""

    text = "猫 が ソファ で 寝ている"

    tokens = tokenize(text)
    token_ids = build_token_ids(tokens)

    # これは学習用に手で用意したEmbedding
    # 実際のLLMでは学習によってEmbeddingが獲得される
    embeddings = {
        "猫": [0.9, 0.1],
        "が": [0.1, 0.1],
        "ソファ": [0.7, 0.3],
        "で": [0.1, 0.2],
        "寝ている": [0.8, 0.7],
    }
    
    print("=" * 60)
    print("TokenとEmbedding")
    print("=" * 60)
    print(f"文章: {text}")
    print(f"Token: {tokens}")
    print(f"Token ID: {token_ids}")

    for token in tokens:
        print(
            f"Token: {token}, "
            f"Embedding: {embeddings[token]}"
        )
        
# 7. Attentionのデモ
def run_attention_demo()->None:
    """Query、Key、Valueを使ったAttentionを実行する。"""

    # 現在注目しているTokenのQuery
    query = [1.0, 0.0]

    # 参照候補となるTokenのKey
    keys = [
        [1.0, 0.0],
        [0.5, 0.5],
        [0.0, 1.0],
    ]

    # 各Tokenが持っている実際の情報
    values = [
        [10.0, 0.0],
        [0.0, 10.0],
        [5.0, 5.0],
    ]

    raw_scores, attention_weights, output = (
        scaled_dot_product_attention(
            query=query,
            keys=keys,
            values=values,
        )
    )

    print()
    print("=" * 60)
    print("Attention")
    print("=" * 60)
    print(f"Query: {query}")
    print(f"Keyとの内積: {raw_scores}")
    print(f"Attention重み: {attention_weights}")
    print(f"最終出力: {output}")

# ============================================================
# 8. mainはデモの呼び出しだけにする
# ============================================================

def main() -> None:
    run_token_demo()
    run_attention_demo()

    tokens = tokenize("猫 が ソファ で 寝ている")
    check_context_window(
        tokens=tokens,
        max_tokens=10,
    )


if __name__ == "__main__":
    main()
