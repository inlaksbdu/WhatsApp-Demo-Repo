# from tools.tools import BankingTools
# import asyncio
# from loguru import logger

# async def test_account_creation_flow():
#     banking_tools = BankingTools()
    
#     try:
#         # Step 1: Generate OTP
#         logger.info("Step 1: Generating OTP")
#         otp_response = await banking_tools.generate_otp({
#             "mobile_number": "+233559158793"  # Replace with test phone number
#         })
        
#         if not otp_response or "identifier" not in otp_response:
#             logger.error("Failed to generate OTP")
#             return
        
#         identifier = otp_response["identifier"]
#         logger.info(f"OTP generated successfully. Identifier: {identifier}")
        
#         # In a real scenario, the user would receive the OTP via SMS/WhatsApp
#         # For testing, we'll ask for the OTP manually
#         print("\nCheck your phone for the OTP code")
#         otp_code = input("Enter the OTP code you received: ")
        
#         # Step 2: Verify OTP and get account creation link
#         logger.info("Step 2: Verifying OTP")
#         verify_response = await banking_tools.verify_otp_and_generate_create_account_link({
#             "identifier": identifier,
#             "otp_code": otp_code
#         })
        
#         if not verify_response or "error" in verify_response.lower():
#             logger.error(f"OTP verification failed: {verify_response}")
#             return
            
#         logger.info(f"Account creation link generated: {verify_response}")
        
#         # Step 3: Create account (this would normally happen through the web interface)
#         # Just showing the URL where the user would go to complete account creation
#         print(f"\nAccount creation link: {verify_response}")
#         print("User would complete account creation through the web interface")
        
#     except Exception as e:
#         logger.error(f"Error in account creation flow: {str(e)}")

# def run_test():
#     asyncio.run(test_account_creation_flow())

# if __name__ == "__main__":
#     run_test()

# import asyncio
# from googletrans import Translator
# import logging
# from typing import Optional

# async def translate_text(text: str, target_language: str) -> Optional[str]:
#     """
#     Am tool to help you translate your english response to amharic and afan Oromo.

#     Args:
#         english_response: The text to be translated
#         target_language: The language code to translate to (e.g., 'am' for amharic, 'es' for Spanish)

#     Returns:
#         Optional[str]: Translated text, or None if translation fails
#     """
#     try:
#         # Create translator instance
#         translator = Translator()

#         # Translate the text
#         translation = await translator.translate(text, dest=target_language)

#         return translation.text

#     except Exception as e:
#         logging.error(f"Translation error: {str(e)}")
#         return None

# # Example usage
# async def main():
#     # Configure logging
#     logging.basicConfig(level=logging.INFO)

#     # Example translations
#     text = "Hello, how are you?"
    
#     # Translate to French
#     french_translation = await translate_text(text, 'am')
#     print(f"French: {french_translation}")

#     # Translate to Spanish
#     spanish_translation = await translate_text(text, 'om')
#     print(f"Spanish: {spanish_translation}")

#     # Translate to German
#     german_translation = await translate_text(text, 'de')
#     print(f"German: {german_translation}")

# # Run the async main function
# if __name__ == "__main__":
#     asyncio.run(main())

# import os

# from google.cloud.speech_v2 import SpeechClient
# from google.cloud.speech_v2.types import cloud_speech
# import os

# from google.cloud.speech_v2 import SpeechClient
# from google.cloud.speech_v2.types import cloud_speech

# client = SpeechClient.from_service_account_file("inbound-planet-452716-i3-06ff9e780898")

# PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
# print(PROJECT_ID)

# def create_recognizer(recognizer_id: str) -> cloud_speech.Recognizer:
#     """Сreates a recognizer with an unique ID and default recognition configuration.
#     Args:
#         recognizer_id (str): The unique identifier for the recognizer to be created.
#     Returns:
#         cloud_speech.Recognizer: The created recognizer object with configuration.
#     """
#     # Instantiates a client
#     client = SpeechClient()

#     request = cloud_speech.CreateRecognizerRequest(
#         parent=f"projects/{PROJECT_ID}/locations/global",
#         recognizer_id=recognizer_id,
#         recognizer=cloud_speech.Recognizer(
#             default_recognition_config=cloud_speech.RecognitionConfig(
#                 language_codes=["en-US"], model="long"
#             ),
#         ),
#     )
#     # Sends the request to create a recognizer and waits for the operation to complete
#     operation = client.create_recognizer(request=request)
#     recognizer = operation.result()

#     print("Created Recognizer:", recognizer.name)
#     return recognizer




# def transcribe_reuse_recognizer(
#     audio_file: str,
#     recognizer_id: str,
# ) -> cloud_speech.RecognizeResponse:
#     """Transcribe an audio file using an existing recognizer.
#     Args:
#         audio_file (str): Path to the local audio file to be transcribed.
#             Example: "resources/audio.wav"
#         recognizer_id (str): The ID of the existing recognizer to be used for transcription.
#     Returns:
#         cloud_speech.RecognizeResponse: The response containing the transcription results.
#     """
#     # Instantiates a client
#     client = SpeechClient()

#     # Reads a file as bytes
#     with open(audio_file, "rb") as f:
#         audio_content = f.read()

#     request = cloud_speech.RecognizeRequest(
#         recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/{recognizer_id}",
#         content=audio_content,
#     )

#     # Transcribes the audio into text
#     response = client.recognize(request=request)

#     for result in response.results:
#         print(f"Transcript: {result.alternatives[0].transcript}")

#     return response


# if __name__ == "__main__":
#     recognizer_id = "my-rec"
#     audio_file = "resources/audio.wav"

    # Create a recognizer
    # recognizer = create_recognizer(recognizer_id)

    # Transcribe an audio file using the created


import os
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(GOOGLE_APPLICATION_CREDENTIALS)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
from langchain_google_community import SpeechToTextLoader


import os
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

credential_path = GOOGLE_APPLICATION_CREDENTIALS
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

def transcribe_file_v2(
    project_id: str,
    audio_file: str,
) -> cloud_speech.RecognizeResponse:
    
    print(project_id)
    # Instantiates a client
    client = SpeechClient()

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["fr-FR"],
        model="long",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/global/recognizers/_",
        config=config,
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

transcribe_file_v2("inbound-planet-452716-i3", "common_voice_ha_26699728.mp3")

# def load_speech_to_text(project_id, file_path):
#     try:
#         # Ensure credentials are set
#         if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
#             raise ValueError("Google Application Credentials not set. Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable.")
        
#         # Create loader
#         loader = SpeechToTextLoader(project_id=project_id, file_path=file_path)
        
#         # Load documents
#         docs = loader.load()
#         return docs
    
#     except Exception as e:
#         print(f"Error loading speech-to-text: {e}")
#         print("Troubleshooting steps:")
#         print("1. Verify GOOGLE_APPLICATION_CREDENTIALS is set correctly")
#         print("2. Ensure the service account has proper permissions")
#         print("3. Check that the file path and project ID are correct")
#         return None

# # Usage
# project_id = "inbound-planet-452716-i3"
# file_path = "common_voice_ha_26699728.mp3"
# documents = load_speech_to_text(project_id, file_path)

# if documents:
#     for doc in documents:
#         print(doc)


# # from langchain_google_community import SpeechToTextLoader

# # project_id = "inbound-planet-452716-i3"
# # file_path = "common_voice_ha_26699728.mp3"
# # # or a local file path: file_path = "./audio.wav"

# # loader = SpeechToTextLoader(project_id=project_id, file_path=file_path)

# # docs = loader.load()
# # docs