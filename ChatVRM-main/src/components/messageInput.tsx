import { useEffect, useCallback } from "react";
import { IconButton } from "./iconButton";
import { useVoskBrowser } from "../hooks/useVoskBrowser";

type Props = {
  userMessage: string;
  isChatProcessing: boolean;
  onChangeUserMessage: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
  onKeyDownUserMessage: (event: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onClickSendButton: (event: React.MouseEvent<HTMLButtonElement>) => void;
};
export const MessageInput = ({
  userMessage,
  isChatProcessing,
  onChangeUserMessage,
  onKeyDownUserMessage,
  onClickSendButton,
}: Props) => {
  const { isRecording, isLoading, transcript, error, modelLoaded, start, stop, reset } = useVoskBrowser({
    modelPath: '/models/vosk-model-small-cn-0.22.tar.gz'
  });

  // 当语音识别完成后（停止录音），将识别结果填入输入框
  useEffect(() => {
    console.log('[MessageInput] transcript 更新:', transcript, 'isRecording:', isRecording);
    
    // 实时显示识别结果（包括录音过程中的部分结果）
    if (transcript) {
      console.log('[MessageInput] 更新输入框内容为:', transcript);
      const event = { target: { value: transcript } } as React.ChangeEvent<HTMLInputElement>;
      onChangeUserMessage(event);
      
      // 只有在停止录音后才清空 transcript 状态
      if (!isRecording) {
        console.log('[MessageInput] 录音已停止，准备清空 transcript');
        // 使用 setTimeout 确保 onChangeUserMessage 已经执行完成
        setTimeout(() => {
          reset();
        }, 100);
      }
    }
  }, [transcript, isRecording, onChangeUserMessage, reset]);

  const handleMicClick = useCallback(() => {
    if (isRecording) {
      stop();
    } else {
      start();
    }
  }, [isRecording, start, stop]);

  const getMicButtonTooltip = () => {
    if (!modelLoaded) return "模型加载中...";
    if (isLoading) return "准备中...";
    if (error) return "语音识别出错";
    if (isRecording) return "停止录音";
    return "开始录音";
  };
  return (
    <div className="absolute bottom-0 z-20 w-screen">
      <div className="bg-base text-black">
        <div className="mx-auto max-w-4xl p-16">
          <div className="grid grid-flow-col gap-[8px] grid-cols-[min-content_1fr_min-content]">
            <IconButton
              iconName="24/Microphone"
              className="bg-secondary hover:bg-secondary-hover active:bg-secondary-press disabled:bg-secondary-disabled"
              isProcessing={isRecording || isLoading}
              disabled={!modelLoaded || isLoading || isChatProcessing}
              onClick={handleMicClick}
              tooltip={getMicButtonTooltip()}
            />
            <input
              id="userMessage"
              name="userMessage"
              type="text"
              placeholder={isRecording ? "正在录音..." : "Message"}
              onChange={onChangeUserMessage}
              onKeyDown={onKeyDownUserMessage}
              disabled={isChatProcessing}
              readOnly={isRecording}
              className="bg-surface1 hover:bg-surface1-hover focus:bg-surface1 disabled:bg-surface1-disabled disabled:text-primary-disabled rounded-16 w-full px-16 text-text-primary typography-16 font-M_PLUS_2 font-bold disabled"
              value={userMessage}
            ></input>

            <IconButton
              iconName="24/Send"
              className="bg-secondary hover:bg-secondary-hover active:bg-secondary-press disabled:bg-secondary-disabled"
              isProcessing={isChatProcessing}
              disabled={isChatProcessing || !userMessage}
              onClick={onClickSendButton}
            />
          </div>
        </div>
        <div className="py-4 bg-[#413D43] text-center text-white font-Montserrat">
          powered by&nbsp;
          <a target="_blank" href="https://openrouter.ai/" className="underline">
            OpenRouter
          </a>,&nbsp;
          <a target="_blank" href="https://beta.elevenlabs.io/" className="underline">
            ElevenLabs
          </a>,&nbsp;
          <a target="_blank" href="https://vroid.com/" className="underline">
            VRoid
          </a>
        </div>
      </div>
    </div>
  );
};
