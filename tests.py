import unittest
from unittest.mock import patch, MagicMock
import os
import wave
import math
import struct
import tempfile
import json
import subprocess
from app import app, chunk_text, assemble_video, check_ffmpeg

class TestTTSApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_1_chunk_text_basic(self):
        """Testa se o chunk_text divide corretamente os parágrafos ignorando os muito curtos."""
        text = "Paragrafo 1.\n\nParagrafo 2 longo o suficiente para não ser ignorado.\n\nCurto.\n\nParagrafo 4 maior que dez caracteres."
        chunks = chunk_text(text, max_chars=600)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "Paragrafo 1.")
        self.assertEqual(chunks[1], "Paragrafo 2 longo o suficiente para não ser ignorado.")
        self.assertEqual(chunks[2], "Paragrafo 4 maior que dez caracteres.")

    def test_2_chunk_text_subdivision(self):
        """Testa se blocos enormes são particionados pelo chunk_text sem ultrapassar o max_chars."""
        # Cria um paragrafo longo com palavras, para o chunk_text poder cortar nos espacos
        long_para = ("Palavra longa com varios caracteres espacados adequadamente " * 20) # > 1000 chars
        chunks = chunk_text(long_para, max_chars=600)
        self.assertTrue(len(chunks) >= 2)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 600)

    def test_3_check_ffmpeg(self):
        """Verifica se o sistema reconhece a instalação do FFmpeg."""
        self.assertTrue(check_ffmpeg())

    def test_4_assemble_video_single_and_slideshow(self):
        """Testa a geração de vídeo usando o FFmpeg com 1 ou múltiplas imagens."""
        if not check_ffmpeg():
            self.skipTest("FFmpeg is missing")

        def generate_dummy_wav(path, duration=1.0):
            sample_rate = 24000
            num_samples = int(sample_rate * duration)
            with wave.open(path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                # Gera um sinal senoidal para termos áudio real simulado
                for i in range(num_samples):
                    value = int(32767.0 * math.cos(2.0 * math.pi * 440.0 * (i / sample_rate)))
                    wf.writeframesraw(struct.pack('<h', value))

        def generate_dummy_image(path):
            import subprocess
            subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=640x480', '-frames:v', '1', path], capture_output=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "test.wav")
            img1 = os.path.join(tmpdir, "img1.jpg")
            img2 = os.path.join(tmpdir, "img2.jpg")
            
            # Gera mock de aúdio e imagens via Python local e FFMPEG 
            generate_dummy_wav(wav_path, duration=0.4)
            generate_dummy_image(img1)
            generate_dummy_image(img2)
            
            # Teste 1: Única imagem (Estático)
            out1 = os.path.join(tmpdir, "out1.mp4")
            res1 = assemble_video(wav_path, [img1], out1)
            self.assertTrue(res1)
            self.assertTrue(os.path.exists(out1))
            self.assertGreater(os.path.getsize(out1), 1000) # garante que não ta vazio
            
            # Teste 2: Slideshow com múltiplas imagens e crossfade
            out2 = os.path.join(tmpdir, "out2.mp4")
            res2 = assemble_video(wav_path, [img1, img2], out2)
            self.assertTrue(res2)
            self.assertTrue(os.path.exists(out2))
            self.assertGreater(os.path.getsize(out2), 1000)

            # Teste 3: Export vertical para Shorts
            out3 = os.path.join(tmpdir, "short.mp4")
            res3 = assemble_video(wav_path, [img1], out3, format="short")
            self.assertTrue(res3)
            self.assertTrue(os.path.exists(out3))
            self.assertGreater(os.path.getsize(out3), 1000)

            probe = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height',
                    '-of', 'json',
                    out3
                ],
                capture_output=True, text=True, timeout=30
            )
            dims = json.loads(probe.stdout)["streams"][0]
            self.assertEqual(dims["width"], 1080)
            self.assertEqual(dims["height"], 1920)

    @patch('app.genai.Client')
    @patch('newspaper.Article')  # Agora mockando corretamente de onde a biblioteca vem globalmente
    def test_5_scriptify_mocked(self, MockArticle, MockClient):
        """Testa o endpoint de roteirização mockando as bibliotecas newspaper e genai para NÃO gastar tokens."""
        # 1. Mock do Article (newspaper3k)
        mock_article_instance = MagicMock()
        mock_article_instance.text = "This is a dummy article text that is long enough to bypass the min character limit check in the scriptify endpoint. " * 3
        MockArticle.return_value = mock_article_instance
        
        # 2. Mock do Gemini API
        mock_gemini_client = MagicMock()
        MockClient.return_value = mock_gemini_client
        mock_response = MagicMock()
        
        # Simula resposta do Gemini com Script e os Prompts
        mock_response.text = "Here is the generated script.\n===IMAGE_PROMPTS===\n[\"prompt1\", \"prompt2\"]"
        mock_gemini_client.models.generate_content.return_value = mock_response

        # 3. Executar rota (Mock)
        response = self.client.post('/scriptify', json={'api_key': 'fake_key', 'url': 'http://example.com'})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['script'], "Here is the generated script.")
        self.assertEqual(len(data['image_prompts']), 2)

    @patch('app.genai.Client')
    def test_6_shorts_scriptify_mocked(self, MockClient):
        """Testa a geração de Shorts sem gastar tokens."""
        mock_gemini_client = MagicMock()
        MockClient.return_value = mock_gemini_client
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "shorts": [
                {
                    "id": "short_1",
                    "title": "The Spy Plane Nobody Could Catch",
                    "hook": "This aircraft did not dodge missiles.",
                    "script": "This aircraft did not dodge missiles. It outran them. Watch the full documentary for the whole story.",
                    "cta": "Watch the full documentary for the whole story.",
                    "image_prompts": [
                        {"cue": "Opening", "prompt": "Vertical 9:16 black and white cinematic spy plane image"}
                    ],
                    "broll_keywords": ["SR-71", "Blackbird", "Cold War"]
                },
                {
                    "id": "short_2",
                    "title": "Fuel on the Runway",
                    "hook": "Before takeoff, it leaked fuel.",
                    "script": "Before takeoff, it leaked fuel. The full documentary explains why.",
                    "cta": "Watch the full documentary.",
                    "image_prompts": [],
                    "broll_keywords": ["hangar", "runway"]
                }
            ]
        })
        mock_gemini_client.models.generate_content.return_value = mock_response

        response = self.client.post('/shorts/scriptify', json={
            'api_key': 'fake_key',
            'script': 'This is a long documentary script about a declassified military aircraft. ' * 20,
            'count': 2,
            'duration_seconds': 60,
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['duration_seconds'], 60)
        self.assertEqual(len(data['shorts']), 2)
        self.assertEqual(data['shorts'][0]['image_prompts'][0]['cue'], "Opening")
        self.assertEqual(data['shorts'][0]['broll_keywords'][0], "SR-71")

    @patch('app.genai.Client')
    def test_7_tiktok_shorts_duration_mocked(self, MockClient):
        """Garante que a opção TikTok usa 65s e pede vídeo acima de 1 minuto."""
        mock_gemini_client = MagicMock()
        MockClient.return_value = mock_gemini_client
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "shorts": [
                {
                    "id": "short_1",
                    "title": "One Minute Spy Plane Story",
                    "hook": "The mission almost failed before takeoff.",
                    "script": "The mission almost failed before takeoff. This longer version gives the full setup, the danger, and the payoff before sending viewers to the full documentary.",
                    "cta": "Watch the full documentary for the complete story.",
                    "image_prompts": [],
                    "broll_keywords": ["spy plane", "runway"]
                }
            ]
        })
        mock_gemini_client.models.generate_content.return_value = mock_response

        response = self.client.post('/shorts/scriptify', json={
            'api_key': 'fake_key',
            'script': 'This is a long documentary script about a declassified military aircraft. ' * 20,
            'count': 3,
            'duration_seconds': 65,
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['duration_seconds'], 65)
        self.assertEqual(data['count'], 1)

        sent_prompt = mock_gemini_client.models.generate_content.call_args.kwargs['contents']
        self.assertIn('Platform: TikTok Creator Rewards.', sent_prompt)
        self.assertIn('between 61 and 65 seconds', sent_prompt)

    @patch('app.time.sleep')
    @patch('app.chunk_text')
    @patch('app.genai.Client')
    def test_8_generate_stream_waits_between_new_chunks(self, MockClient, mock_chunk_text, mock_sleep):
        """Garante chunking maior e throttling SSE entre chunks gerados."""
        mock_chunk_text.return_value = [
            "First chunk with enough content to synthesize.",
            "Second chunk with enough content to synthesize.",
        ]

        mock_gemini_client = MagicMock()
        MockClient.return_value = mock_gemini_client

        mock_response = MagicMock()
        mock_response.candidates[0].content.parts[0].inline_data.data = b'\x00\x00'
        mock_gemini_client.models.generate_content.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir, patch('app.TMP_SESSIONS', tmpdir):
            response = self.client.post('/generate-stream', json={
                'api_key': 'fake_key',
                'text': 'Long script body',
                'voice': 'Charon',
                'session_id': 'test-session',
            })

        self.assertEqual(response.status_code, 200)
        mock_chunk_text.assert_called_once_with('Long script body', max_chars=9500)
        mock_sleep.assert_called_once_with(62)
        self.assertEqual(mock_gemini_client.models.generate_content.call_count, 2)

        payload = response.data.decode('utf-8')
        self.assertIn('"type": "waiting"', payload)
        self.assertIn('"seconds": 62', payload)

if __name__ == '__main__':
    unittest.main()
