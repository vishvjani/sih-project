import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface HologramScannerProps {
  isScanning?: boolean;
  className?: string;
  hasImage?: boolean;
}

export const HologramScanner: React.FC<HologramScannerProps> = ({
  isScanning = false,
  className = '',
  hasImage = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    cube: THREE.LineSegments;
    innerCore: THREE.Mesh;
    scanPlane: THREE.Mesh;
    particles: THREE.Points;
    rings: THREE.Group;
    animFrameId: number;
    mouseX: number;
    mouseY: number;
  } | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 300;
    const height = container.clientHeight || 300;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 8);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 1. Outer 3D Cyber Wireframe Geodesic Box
    const boxGeometry = new THREE.BoxGeometry(3.2, 3.2, 3.2);
    const boxEdges = new THREE.EdgesGeometry(boxGeometry);
    const boxMaterial = new THREE.LineBasicMaterial({
      color: 0x96E071,
      transparent: true,
      opacity: 0.45,
      linewidth: 1.5,
    });
    const cube = new THREE.LineSegments(boxEdges, boxMaterial);
    scene.add(cube);

    // 2. Inner Glowing Core (Icosahedron representing AI Latent Space)
    const coreGeometry = new THREE.IcosahedronGeometry(1.2, 1);
    const coreMaterial = new THREE.MeshBasicMaterial({
      color: 0x75da4c,
      wireframe: true,
      transparent: true,
      opacity: 0.65,
    });
    const innerCore = new THREE.Mesh(coreGeometry, coreMaterial);
    scene.add(innerCore);

    // 3. 3D Laser Scanning Plane
    const planeGeo = new THREE.PlaneGeometry(3.6, 3.6);
    const planeMat = new THREE.MeshBasicMaterial({
      color: 0x96E071,
      transparent: true,
      opacity: 0.2,
      side: THREE.DoubleSide,
    });
    const scanPlane = new THREE.Mesh(planeGeo, planeMat);
    scanPlane.rotation.x = Math.PI / 2;
    scene.add(scanPlane);

    // 4. Concentric Orbital Rings
    const rings = new THREE.Group();
    for (let i = 0; i < 3; i++) {
      const ringGeo = new THREE.RingGeometry(1.9 + i * 0.4, 1.93 + i * 0.4, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color: i % 2 === 0 ? 0x96E071 : 0x38bdf8,
        transparent: true,
        opacity: 0.25 - i * 0.05,
        side: THREE.DoubleSide,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = (Math.PI / 3) * (i + 1);
      ringMesh.rotation.y = (Math.PI / 4) * (i + 1);
      rings.add(ringMesh);
    }
    scene.add(rings);

    // 5. Floating Particle Matrix (Data Nodes)
    const particleCount = 140;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 6;
      positions[i + 1] = (Math.random() - 0.5) * 6;
      positions[i + 2] = (Math.random() - 0.5) * 6;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMat = new THREE.PointsMaterial({
      color: 0xb3f595,
      size: 0.06,
      transparent: true,
      opacity: 0.7,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    let mouseX = 0;
    let mouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      mouseX = x * 2;
      mouseY = y * 2;
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Resize observer
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let clock = new THREE.Clock();
    const animate = () => {
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse parallax
      camera.position.x += (mouseX * 1.5 - camera.position.x) * 0.05;
      camera.position.y += (-mouseY * 1.5 - camera.position.y) * 0.05;
      camera.lookAt(0, 0, 0);

      // Rotation speeds
      const speed = isScanning ? 2.5 : 1.0;
      cube.rotation.x += 0.005 * speed;
      cube.rotation.y += 0.008 * speed;

      innerCore.rotation.x -= 0.009 * speed;
      innerCore.rotation.y -= 0.012 * speed;

      rings.rotation.z += 0.004 * speed;
      particles.rotation.y += 0.002 * speed;

      // Scanning plane movement
      const scanY = Math.sin(elapsedTime * (isScanning ? 3.5 : 1.5)) * 1.6;
      scanPlane.position.y = scanY;
      scanPlane.material.opacity = isScanning ? 0.45 + Math.sin(elapsedTime * 10) * 0.15 : 0.2;

      // Color shifts when scanning
      if (isScanning) {
        boxMaterial.color.setHex(0xb3f595);
        boxMaterial.opacity = 0.8;
      } else {
        boxMaterial.color.setHex(0x96E071);
        boxMaterial.opacity = 0.45;
      }

      renderer.render(scene, camera);
      sceneRef.current!.animFrameId = requestAnimationFrame(animate);
    };

    sceneRef.current = {
      scene,
      camera,
      renderer,
      cube,
      innerCore,
      scanPlane,
      particles,
      rings,
      animFrameId: requestAnimationFrame(animate),
      mouseX: 0,
      mouseY: 0,
    };

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      if (sceneRef.current) {
        cancelAnimationFrame(sceneRef.current.animFrameId);
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [isScanning]);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    >
      {/* Visual cybernetic HUD overlay corners */}
      <div className="absolute top-2 left-2 flex items-center gap-1 font-mono text-[9px] text-[#96E071]/70 tracking-widest pointer-events-none select-none">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#96E071] animate-ping" />
        <span>3D_SCAN_MATRIX // {isScanning ? 'ACTIVE_PASS' : hasImage ? 'ANALYZED' : 'STANDBY'}</span>
      </div>
      <div className="absolute bottom-2 right-2 font-mono text-[8px] text-gray-500 tracking-wider pointer-events-none select-none">
        LATENT_SPACE_DIM [768] // 60 FPS
      </div>
    </div>
  );
};
