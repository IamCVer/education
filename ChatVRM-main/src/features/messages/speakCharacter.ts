import { wait } from "@/utils/wait";
import { synthesizeVoice } from "../elevenlabs/elevenlabs";
import { synthesizeLocalVoice } from "../tts/localTts";
import { getAuthToken } from "../chat/fastApiChat";
import { Viewer } from "../vrmViewer/viewer";
import { Screenplay } from "./messages";
import { Talk } from "./messages";
import { ElevenLabsParam } from "../constants/elevenLabsParam";

const createSpeakCharacter = () => {
  let lastTime = 0;
  let prevFetchPromise: Promise<unknown> = Promise.resolve();
  let prevSpeakPromise: Promise<unknown> = Promise.resolve();

  return (
    screenplay: Screenplay,
    elevenLabsKey: string,
    elevenLabsParam: ElevenLabsParam,
    viewer: Viewer,
    onStart?: () => void,
    onComplete?: () => void
  ) => {
    const fetchPromise = prevFetchPromise.then(async () => {
      const now = Date.now();
      if (now - lastTime < 1000) {
        await wait(1000 - (now - lastTime));
      }

      // 🔧 优先使用本地 TTS，即使没有 elevenLabsKey
      const token = getAuthToken();
      const buffer = await fetchAudio(screenplay.talk, elevenLabsKey, elevenLabsParam).catch((error) => {
        console.error("❌ TTS 失败:", error);
        return null;
      });
      lastTime = Date.now();
      return buffer;
    });

    prevFetchPromise = fetchPromise;
    prevSpeakPromise = Promise.all([fetchPromise, prevSpeakPromise]).then(([audioBuffer]) => {
      onStart?.();
      if (!audioBuffer) {
        // pass along screenplay to change avatar expression
        return viewer.model?.speak(null, screenplay);
      }
      return viewer.model?.speak(audioBuffer, screenplay);
    });
    prevSpeakPromise.then(() => {
      onComplete?.();
    });
  };
}

export const speakCharacter = createSpeakCharacter();

export const fetchAudio = async (
  talk: Talk, 
  elevenLabsKey: string,
  elevenLabsParam: ElevenLabsParam,
  ): Promise<ArrayBuffer> => {
  
  // 优先使用本地 TTS
  const token = getAuthToken();
  if (token) {
    try {
      console.log('使用本地 TTS 服务');
      const ttsVoice = await synthesizeLocalVoice(talk.message, token);
      const url = ttsVoice.audio;
      
      if (!url) {
        throw new Error("TTS URL 为空");
      }
      
      const resAudio = await fetch(url);
      const buffer = await resAudio.arrayBuffer();
      return buffer;
    } catch (error) {
      console.error('本地 TTS 失败，尝试降级到 ElevenLabs:', error);
      // 降级到 ElevenLabs（如果配置了 API Key）
    }
  }
  
  // 降级方案：使用 ElevenLabs
  if (elevenLabsKey && elevenLabsKey.trim() !== "") {
    const ttsVoice = await synthesizeVoice(
      talk.message,
      talk.speakerX,
      talk.speakerY,
      talk.style,
      elevenLabsKey,
      elevenLabsParam
    );
    const url = ttsVoice.audio;
    
    if (url == null) {
      throw new Error("Something went wrong");
    }
    
    const resAudio = await fetch(url);
    const buffer = await resAudio.arrayBuffer();
    return buffer;
  }
  
  throw new Error("无可用的 TTS 服务");
};
