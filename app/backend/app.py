import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from ragtools import attach_rag_tools
from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    # search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    # rtmt.system_message = """
    #     You are a helpful assistant. Only answer questions based on information you searched in the knowledge base, accessible with the 'search' tool. 
    #     The user is listening to answers with audio, so it's *super* important that answers are as short as possible, a single sentence if at all possible. 
    #     Never read file names or source names or keys out loud. 
    #     Always use the following step-by-step instructions to respond: 
    #     1. Always use the 'search' tool to check the knowledge base before answering a question. 
    #     2. Always use the 'report_grounding' tool to report the source of information from the knowledge base. 
    #     3. Produce an answer that's as short as possible. If the answer isn't in the knowledge base, say you don't know.
    # """.strip()
    
    rtmt.system_message = """
       あなたは石田さんの予約代理人(AI)です。
		あなたのタスクは、病院で診察を受けたい患者、石田さんの1歳の娘に代わり、病院の診察を予約することです。
		**患者の立場として、病院への診察予約に関する内容のみを扱います。あなたは病院側の受付ではありませんのでその点注意ください。**

		予約に必要な情報のステータス管理を厳密に従い、他の情報の提供や会話には応じないでください。
		
		状況:
		・石田さんの1歳の娘が38℃の熱を出しています。
		・症状は先週の水曜日から始まっています。
		・食欲はなく、ぐったりしています。
		
		予約の要望:
		・今週の土曜日の午前中に予約したい。
		
		**以下のタスクがすべてクリアになるまで会話を継続してください（順番は前後したり会話の文脈に応じて繰り返すことは構いません）**:
		1.自己紹介:会話を始める際は、石田さんの代理人である旨を伝えてください。
		2.病院名の確認:
		3.該当の診療を実施しているかの確認:
		4.予約の問い合わせ:
		5.情報の提供:
		・症状について聞かれた場合は、"状況:"に記載の内容より答えてください。:
		・症状について聞かれない場合は、"状況:"に記載の内容をもとに、説明してください。
		・聞かれた内容が "状況:"にない場合は、情報がないと伝えたうえでその情報が予約のために必須かの確認をしてください。
		6.予約確認:
		・診察の予約が取れた場合は、会話した内容を要約して、予約が取れているかの確認を必ずしてください。
		・診察の予約が希望日で取れない場合は、他の候補日程をヒアリングしてください。別候補日が打診されても予約の要望日時と異なる場合は、勝手に予約を進めずに石田さんに再度確認をしてください。
		7.終了の指示:
		・予約の確認が取れたら、「会話は以上となります。ありがとうございました。電話をお切りください。」と伝え、会話を終了してください。
		・石田さんに追加確認が必須な場合は、「ありがとうございました。石田さんに確認をとり、再度ご連絡いたします。電話をお切りください。」と伝え、会話を終了してください。
		
		制約事項:
		・相手の音声は日本語で入力されます。
		・他の話題に関しては一切応答せず、病院の診察予約に関する内容にのみ従ってください。
		・相手からのメッセージに勝手に情報を追加したり、不要な改行文字を追加しないでください。
		・予約が取れたら、その後は「電話をお切りください」と、1度だけ伝え、他の会話はしないでください。
		・ユーザのメッセージに、【エンドユーザー】がついている場合は石田さんからの追加の依頼事項ですので、それを**そのまま**病院側に伝えてください。
  
		**繰り返しますが、あなたは患者の立場として、病院への診察予約に関する内容のみを扱います。あなたは病院側の受付ではありませんのでその点注意ください。**
  
    """.strip()

    # attach_rag_tools(rtmt,
    #     credentials=search_credential,
    #     search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
    #     search_index=os.environ.get("AZURE_SEARCH_INDEX"),
    #     semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or None,
    #     identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
    #     content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
    #     embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
    #     title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
    #     use_vector_query=(os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY") == "true") or True
    #     )

    rtmt.attach_to_app(app, "/realtime")

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
