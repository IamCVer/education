import React, { useEffect, useState, cache } from "react";
import { IconButton } from "./iconButton";
import { TextButton } from "./textButton";
import { Message } from "@/features/messages/messages";
import {
  KoeiroParam,
  PRESET_A,
  PRESET_B,
  PRESET_C,
  PRESET_D,
} from "@/features/constants/koeiroParam";
import { Link } from "./link";
import { getVoices } from "@/features/elevenlabs/elevenlabs";
import { ElevenLabsParam } from "@/features/constants/elevenLabsParam";
import { RestreamTokens } from "./restreamTokens";
import { LoginDialog } from "./loginDialog";
import Cookies from 'js-cookie';

type Props = {
  openAiKey: string;
  elevenLabsKey: string;
  openRouterKey: string;
  systemPrompt: string;
  chatLog: Message[];
  elevenLabsParam: ElevenLabsParam;
  koeiroParam: KoeiroParam;
  onClickClose: () => void;
  onChangeAiKey: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onChangeOpenRouterKey: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onChangeElevenLabsKey: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onChangeElevenLabsVoice: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  onChangeSystemPrompt: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onChangeChatLog: (index: number, text: string) => void;
  onChangeKoeiroParam: (x: number, y: number) => void;
  onClickOpenVrmFile: () => void;
  onClickResetChatLog: () => void;
  onClickResetSystemPrompt: () => void;
  backgroundImage: string;
  onChangeBackgroundImage: (image: string) => void;
  onRestreamTokensUpdate?: (tokens: { access_token: string; refresh_token: string; } | null) => void;
  onTokensUpdate: (tokens: any) => void;
  onChatMessage: (message: string) => void;
  onLoginSuccess?: () => void;
};
export const Settings = ({
  openAiKey,
  elevenLabsKey,
  openRouterKey,
  chatLog,
  systemPrompt,
  elevenLabsParam,
  koeiroParam,
  onClickClose,
  onChangeSystemPrompt,
  onChangeAiKey,
  onChangeOpenRouterKey,
  onChangeElevenLabsKey,
  onChangeElevenLabsVoice,
  onChangeChatLog,
  onChangeKoeiroParam,
  onClickOpenVrmFile,
  onClickResetChatLog,
  onClickResetSystemPrompt,
  backgroundImage,
  onChangeBackgroundImage,
  onRestreamTokensUpdate = () => {},
  onTokensUpdate,
  onChatMessage,
  onLoginSuccess,
}: Props) => {

  const [elevenLabsVoices, setElevenLabsVoices] = useState<any[]>([]);

  useEffect(() => {
    // Check if ElevenLabs API key exists before fetching voices
    if (elevenLabsKey) {
      getVoices(elevenLabsKey).then((data) => {
        console.log('getVoices');
        console.log(data);

        const voices = data.voices;
        setElevenLabsVoices(voices);
      });
    }
  }, [elevenLabsKey]); // Added elevenLabsKey as a dependency

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        onChangeBackgroundImage(base64String);
        localStorage.setItem('backgroundImage', base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveBackground = () => {
    onChangeBackgroundImage('');
    localStorage.removeItem('backgroundImage');
  };

  return (
    <div className="absolute z-40 w-full h-full bg-white/80 backdrop-blur ">
      <div className="absolute m-24">
        <IconButton
          iconName="24/Close"
          isProcessing={false}
          onClick={onClickClose}
        ></IconButton>
      </div>
      <div className="max-h-full overflow-auto">
        <div className="text-text1 max-w-3xl mx-auto px-24 py-64 ">
          <div className="my-24 typography-32 font-bold">设置</div>
          
          {/* FastAPI 登录区域 */}
          <div className="my-24">
            <div className="my-16 typography-20 font-bold">FastAPI 后端认证</div>
            <LoginDialog onLoginSuccess={onLoginSuccess || (() => {})} />
            <div className="mt-8 text-text-secondary typography-14">
              登录后可使用本地 LLM 和 TTS 服务
            </div>
          </div>
          
          {/* 隐藏的 API 配置 - 默认使用本地 FastAPI 服务 */}
          {/* 
          <div className="my-24">
            <div className="my-16 typography-20 font-bold">OpenRouter API (降级方案)</div>
            <input
              type="text"
              placeholder="OpenRouter API 密钥"
              value={openRouterKey}
              onChange={onChangeOpenRouterKey}
              className="my-4 px-16 py-8 w-full h-40 bg-surface3 hover:bg-surface3-hover rounded-4 text-ellipsis"
            ></input>
            <div>
              输入您的 OpenRouter API 密钥以启用自定义访问。您可以在&nbsp;
              <Link
                url="https://openrouter.ai/"
                label="OpenRouter 官网"
              />&nbsp;获取 API 密钥。默认情况下，本应用使用自己的 OpenRouter API 密钥供用户试用，但可能会用尽额度需要充值。
            </div>
          </div>
          <div className="my-24">
            <div className="my-16 typography-20 font-bold">ElevenLabs API</div>
            <input
              type="text"
              placeholder="ElevenLabs API 密钥"
              value={elevenLabsKey}
              onChange={onChangeElevenLabsKey}
              className="my-4 px-16 py-8 w-full h-40 bg-surface3 hover:bg-surface3-hover rounded-4 text-ellipsis"
            ></input>
            <div>
              输入您的 ElevenLabs API 密钥以启用语音合成功能。您可以在&nbsp;
              <Link
                url="https://beta.elevenlabs.io/"
                label="ElevenLabs 官网"
              />&nbsp;获取 API 密钥。
            </div>
          </div>
          <div className="my-40">
            <div className="my-16 typography-20 font-bold">
              语音选择
            </div>
            <div className="my-16">
              从 ElevenLabs 的语音中选择（包括自定义语音）：
            </div>
            <div className="my-8">
              <select className="h-40 px-8"
                id="select-dropdown"
                onChange={onChangeElevenLabsVoice}
                value={elevenLabsParam.voiceId}
              >
                {elevenLabsVoices.map((voice, index) => (
                  <option key={index} value={voice.voice_id}>
                    {voice.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          */}
          <div className="my-40">
            <div className="my-16 typography-20 font-bold">
              角色模型
            </div>
            <div className="my-8">
              <TextButton onClick={onClickOpenVrmFile}>打开 VRM</TextButton>
            </div>
          </div>
          <div className="my-40">
            <div className="my-8">
              <div className="my-16 typography-20 font-bold">
                角色设置（系统提示词）
              </div>
              <TextButton onClick={onClickResetSystemPrompt}>
                重置角色设置
              </TextButton>
            </div>

            <textarea
              value={systemPrompt}
              onChange={onChangeSystemPrompt}
              className="px-16 py-8  bg-surface1 hover:bg-surface1-hover h-168 rounded-8 w-full"
            ></textarea>
          </div>
          <div className="my-40">
            <div className="my-16 typography-20 font-bold">
              背景图片
            </div>
            <div className="my-16">选择自定义背景图片：</div>
            <div className="my-8 flex flex-col gap-4">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="my-4"
              />
              {backgroundImage && (
                <div className="flex flex-col gap-4">
                  <div className="my-8">
                    <img
                      src={backgroundImage}
                      alt="背景预览"
                      className="max-w-[200px] rounded-4"
                    />
                  </div>
                  <div className="my-8">
                    <TextButton onClick={handleRemoveBackground}>
                      移除背景
                    </TextButton>
                  </div>
                </div>
              )}
              <div className="text-sm text-gray-600">
                背景图片将保存在您的浏览器中，下次访问时会自动恢复。
              </div>
            </div>
          </div>
          <RestreamTokens onTokensUpdate={onTokensUpdate} onChatMessage={onChatMessage} />
          {chatLog.length > 0 && (
            <div className="my-40">
              <div className="my-8 grid-cols-2">
                <div className="my-16 typography-20 font-bold">对话历史</div>
                <TextButton onClick={onClickResetChatLog}>
                  重置对话历史
                </TextButton>
              </div>
              <div className="my-8">
                {chatLog.map((value, index) => {
                  return (
                    <div
                      key={index}
                      className="my-8 grid grid-flow-col  grid-cols-[min-content_1fr] gap-x-fixed"
                    >
                      <div className="w-[64px] py-8">
                        {value.role === "assistant" ? "角色" : "你"}
                      </div>
                      <input
                        key={index}
                        className="bg-surface1 hover:bg-surface1-hover rounded-8 w-full px-16 py-8"
                        type="text"
                        value={value.content}
                        onChange={(event) => {
                          onChangeChatLog(index, event.target.value);
                        }}
                      ></input>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
