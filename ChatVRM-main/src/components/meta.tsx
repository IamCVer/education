import { buildUrl } from "@/utils/buildUrl";
import Head from "next/head";
export const Meta = () => {
  const title = "智能教育问答系统 - ChatVRM";
  const description =
    "基于 VRM 的 3D 虚拟角色对话系统，支持语音输入、文本对话和语音合成。您可以自定义角色、个性设置和声音调整。";
  const imageUrl = buildUrl("/favicon.png");
  return (
    <Head>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={imageUrl} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={imageUrl} />
      <link rel="icon" type="image/png" href={buildUrl("/favicon.png")} />
    </Head>
  );
};
