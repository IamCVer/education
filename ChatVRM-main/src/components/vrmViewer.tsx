import { useContext, useCallback } from "react";
import { ViewerContext } from "../features/vrmViewer/viewerContext";

export default function VrmViewer() {
  const { viewer } = useContext(ViewerContext);

  // 从本地加载 VRM 模型
  const LOCAL_VRM_URL = '/vrm/pinkgirl.vrm';

  const canvasRef = useCallback(
    (canvas: HTMLCanvasElement) => {
      if (canvas) {
        viewer.setup(canvas);
        
        // 从本地加载 VRM 模型
        try {
          viewer.loadVrm(LOCAL_VRM_URL);
          console.log('Successfully loaded VRM from local:', LOCAL_VRM_URL);
        } catch (error) {
          console.warn('Error loading local VRM:', error);
        }

        // Drag and DropでVRMを差し替え
        canvas.addEventListener("dragover", function (event) {
          event.preventDefault();
        });

        canvas.addEventListener("drop", function (event) {
          event.preventDefault();

          const files = event.dataTransfer?.files;
          if (!files) {
            return;
          }

          const file = files[0];
          if (!file) {
            return;
          }

          const file_type = file.name.split(".").pop();
          if (file_type === "vrm") {
            const blob = new Blob([file], { type: "application/octet-stream" });
            const url = window.URL.createObjectURL(blob);
            viewer.loadVrm(url);
          }
        });
      }
    },
    [viewer]
  );

  return (
    <div className={"absolute top-0 left-0 w-screen h-[100svh] -z-10"}>
      <canvas ref={canvasRef} className={"h-full w-full"}></canvas>
    </div>
  );
}
