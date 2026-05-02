import { MessageInput } from "@/components/messageInput";
import { useState, useEffect, useCallback } from "react";

type Props = {
  isChatProcessing: boolean;
  onChatProcessStart: (text: string) => void;
};

/**
 * テキスト入力と音声入力を提供する（Vosk 离线语音识别）
 *
 * 使用 Vosk 进行离线语音识别，返答文の生成中は入力を無効化する
 *
 */
export const MessageInputContainer = ({
  isChatProcessing,
  onChatProcessStart,
}: Props) => {
  const [userMessage, setUserMessage] = useState("");

  const handleClickSendButton = useCallback(() => {
    onChatProcessStart(userMessage);
  }, [onChatProcessStart, userMessage]);

  useEffect(() => {
    if (!isChatProcessing) {
      setUserMessage("");
    }
  }, [isChatProcessing]);

  return (
    <MessageInput
      userMessage={userMessage}
      isChatProcessing={isChatProcessing}
      onKeyDownUserMessage={(e) => {
        if (e.key === "Enter") {
          handleClickSendButton();
        }
      }}
      onChangeUserMessage={(e) => setUserMessage(e.target.value)}
      onClickSendButton={handleClickSendButton}
    />
  );
};
