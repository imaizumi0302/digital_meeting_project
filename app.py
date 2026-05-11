import streamlit as st
import ollama

st.set_page_config(page_title="デジタル会議システム", layout="wide")
st.title("🛡️ デジタル軍議：ペルソナ選択シミュレーター")

# ペルソナ・データベース
# いくつかデフォルトで役柄を用意しておく
# 役柄を選択すると、自動で名前と厳密な性格設定も自動で表示される
if 'persona_db' not in st.session_state:
    st.session_state.persona_db = {
        "厳格な決裁者": {"name": "一条", "role": "コストと納期に極めて厳格。感情論を嫌い、数字と結果のみを評価する。根性論も辞さない。"},
        "品質第一の技術者": {"name": "工藤", "role": "現場叩き上げのエンジニア。ユーザーの安全とシステムの品質を最優先し、無理なスケジュールには徹底抗戦する。"},
        "バランサー営業": {"name": "真理子", "role": "顧客の顔色と社内の事情の板挟みになりながら、現実的な折衷案を探る交渉のプロ。"},
        "悲観的リスク担当": {"name": "ネガティブ担当", "role": "常に最悪の事態を想定し、あらゆる提案に対して法的・セキュリティ的・炎上リスクを指摘する。"},
        "破天荒なアイデアマン": {"name": "ジョブズもどき", "role": "現状の制約にとらわれず、最新技術や奇抜なアイデアで状況を根本から覆そうと提案する。"}
    }

# プルダウンを変えた時に、名前と性格をそれぞれ正しくセットする処理
def update_persona(index):
    selected = st.session_state[f"select_{index}"]
    if selected != "カスタム（自由入力）":
        st.session_state[f"name_{index}"] = st.session_state.persona_db[selected]["name"]
        st.session_state[f"role_{index}"] = st.session_state.persona_db[selected]["role"]
    else:
        st.session_state[f"name_{index}"] = f"専門家{index+1}"
        st.session_state[f"role_{index}"] = ""

# メモリの初期化
for i in range(5):
    if f"name_{i}" not in st.session_state:
        st.session_state[f"name_{i}"] = f"専門家{i+1}"
    if f"role_{i}" not in st.session_state:
        st.session_state[f"role_{i}"] = ""

# --- サイドバー設定 ---
with st.sidebar:
    # サイドバーのタイトル
    st.header("会議の設定")
    # 一人何回発言をするのかをスライダーで設定
    num_rounds = st.slider("議論の周回数（ラウンド）", 1, 5, 3)
    # 会議に参加する人数をスライダーで選択 
    num_agents = st.slider("参加エージェント数", 2, 5, 3) 
    
    # 画面を分ける線
    st.divider()
    agent_configs = []
    # ペルソナのリストを用意
    persona_options = ["カスタム（自由入力）"] + list(st.session_state.persona_db.keys())
    
    # スライダーで選択して人数分だけ、ペルソナを設定していく
    for i in range(num_agents):
        st.markdown(f"**席 {i+1}**")
        
        # 役柄（テンプレート）の選択
        # この key=f"select_{i}"の部分で、st.session_state の中に select_0 というキーが作られ、初期値の"カスタム(自由入力)"が表示される
        # ここで、selectboxから役柄を選択すると、update_persona関数が呼び出される。
        st.selectbox(f"役柄テンプレート", persona_options, key=f"select_{i}", on_change=update_persona, args=(i,))
        
        # 名前の入力
        name = st.text_input("名前（表示名）", key=f"name_{i}")
        
        # 性格設定の入力
        role = st.text_area("性格設定", key=f"role_{i}", height=100)
        
        agent_configs.append({"name": name, "role": role})
        
        # 新たな役柄の保存
        if st.session_state[f"select_{i}"] == "カスタム（自由入力）" and name and role:
            template_name = st.text_input("💡 この設定のテンプレート名（例：理不尽な顧客）", key=f"template_{i}")
            if template_name:
                if st.button(f"💾 名簿に登録", key=f"save_{i}"):
                    st.session_state.persona_db[template_name] = {"name": name, "role": role}
                    st.success(f"「{template_name}」を登録しました！")
                    st.rerun()
        st.divider()

# --- メイン画面 ---
# 会議の議題を入力
issue = st.text_area("具体的な議題：", height=100)

if st.button("軍議を開始する"):
    if issue:
        # 履歴を1つのテキスト（会議録）として扱う
        if 'transcript' not in st.session_state:
            st.session_state.transcript = ""
        
        st.session_state.transcript = f"議題：{issue}\n\n"
        
        for r in range(num_rounds):
            st.markdown(f"### 🔄 第 {r+1} ラウンド")
            
            for i, config in enumerate(agent_configs):
                avatar_icons = ["👔", "💻", "🤝", "🤖", "🎭"]
                icon = avatar_icons[i % 5]
                
                with st.chat_message(config['name'], avatar=icon):
                    st.markdown(f"**【{config['name']}】**")
                    
                    # プロンプトの設定
                    system_prompt = f"""
                    あなたは以下の人物です。
                    名前：{config['name']}
                    性格：{config['role']}
                    
                    【厳守事項 - これを守らないとシステムエラーになります】
                    1. 挨拶や自己紹介（「〜です」「〜と申します」）は絶対に禁止。
                    2. 安易に相手に同意したり、議論をまとめようとしたりしないでください。
                    3. 必ず前の発言の「矛盾点」や「懸念点」を突き、議論を白熱させてください。
                    4. 具体的な理由を添えて、必ず【150文字以上】の長文で語ってください。
                    """
                    
                    user_prompt = f"""
                    【これまでの会議録】
                    {st.session_state.transcript}
                    
                    上記の会議録を読み、あなたの性格・立場から、一番最後の発言に対して強く反論・または深掘りする意見を述べてください。
                    """
                    
                    messages = [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                    
                    # AIの回答を入れる変数を用意
                    placeholder = st.empty()
                    full_response = ""
                    
                    max_retries = 3 
                    
                    # 上記のプロンプトをLLMに投げて、回答を生成するパート
                    # 80文字以下の回答が返ってきた場合には、3回まで再度回答を生成させる。
                    for attempt in range(max_retries):
                        # 一時的な回答を格納する変数
                        temp_response = ""
                        
                        if attempt > 0:
                            placeholder.caption(f"※短すぎたため考え直し中...（{attempt+1}回目）")

                        # LLMに回答を生成してもらい、回答をストリーミングで表示していく    
                        with st.spinner("思考中..."):
                            stream = ollama.chat(model='gemma2:9b', messages=messages, stream=True)
                            for chunk in stream:
                                word = chunk['message']['content']
                                temp_response += word
                                placeholder.markdown(temp_response + "▌")
                        
                        # 発言が80文字以上かどうかを判定
                        # 80文字以下の場合は、再度回答を生成。
                        if len(temp_response.strip()) >= 80:
                            full_response = temp_response
                            break 
                        else:
                            continue
                    
                    # 3回やり直しても、回答が80文字を万が一超えなかった場合には次の人に進む
                    if len(full_response.strip()) < 80:
                        full_response += "\n（※うまく言語化できませんでした。次の人お願いします）"
                        
                    placeholder.markdown(full_response)
                    
                    # 発言を「会議録テキスト」に追記していく
                    #　これにより、次の人は、議題とそこまでの会話をすべて把握したうえで、回答を生成できるようにする。
                    st.session_state.transcript += f"■ {config['name']}の発言:\n{full_response}\n\n"
                    
        st.success("--- 議論が終了しました ---")
    else:
        st.warning("議題を入力してください。")