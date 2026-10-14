"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import jsQR from "jsqr";
import { CameraOffIcon } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Camera -> canvas -> jsQR. Works in every browser that has getUserMedia;
// stops the stream on unmount and after the first hit.
export function QrScanner({ onScan }: { onScan: (text: string) => void }) {
  const t = useTranslations("emergency.scan");
  const video = useRef<HTMLVideoElement>(null);
  const [denied, setDenied] = useState(false);
  const onScanRef = useRef(onScan);
  useEffect(() => {
    onScanRef.current = onScan;
  });

  useEffect(() => {
    let stream: MediaStream | null = null;
    let raf = 0;
    let done = false;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d", { willReadFrequently: true });

    function tick() {
      const el = video.current;
      if (done || !el || !ctx) return;
      if (el.readyState === el.HAVE_ENOUGH_DATA && el.videoWidth > 0) {
        canvas.width = el.videoWidth;
        canvas.height = el.videoHeight;
        ctx.drawImage(el, 0, 0);
        const image = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const hit = jsQR(image.data, image.width, image.height, {
          inversionAttempts: "dontInvert",
        });
        if (hit?.data) {
          done = true;
          onScanRef.current(hit.data);
          return;
        }
      }
      raf = requestAnimationFrame(tick);
    }

    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        if (done) {
          s.getTracks().forEach((track) => track.stop());
          return;
        }
        stream = s;
        if (video.current) {
          video.current.srcObject = s;
          void video.current.play();
        }
        raf = requestAnimationFrame(tick);
      })
      .catch(() => setDenied(true));
    if (!navigator.mediaDevices) setTimeout(() => setDenied(true), 0);

    return () => {
      done = true;
      cancelAnimationFrame(raf);
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  if (denied) {
    return (
      <Alert variant="destructive">
        <CameraOffIcon />
        <AlertDescription>{t("cameraDenied")}</AlertDescription>
      </Alert>
    );
  }
  return (
    <div className="overflow-hidden rounded-xl border bg-black">
      <video
        ref={video}
        muted
        playsInline
        className="aspect-square w-full object-cover"
        aria-label={t("cameraLabel")}
      />
    </div>
  );
}
