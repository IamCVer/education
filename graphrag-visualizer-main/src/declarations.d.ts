declare module '*.json' {
    const value: any;
    export default value;
  }

// Three.js CSS2DRenderer types
declare module 'three/examples/jsm/renderers/CSS2DRenderer' {
  import { Camera, Scene, Object3D } from 'three';

  export class CSS2DRenderer {
    domElement: HTMLElement;
    constructor();
    setSize(width: number, height: number): void;
    render(scene: Scene, camera: Camera): void;
  }

  export class CSS2DObject extends Object3D {
    element: HTMLElement;
    constructor(element: HTMLElement);
  }
}
  