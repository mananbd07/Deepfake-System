console.log("QBioForge FRAME MODE loaded");

function waitForPlayer() {
  const video = document.querySelector("video");
  if (video) initPanel(video);
  else setTimeout(waitForPlayer, 500);
}

function initPanel(video) {

  if (document.getElementById("qbioforge-panel")) return;

  const panel = document.createElement("div");
  panel.id = "qbioforge-panel";

  panel.style.position = "fixed";
  panel.style.bottom = "30px";
  panel.style.right = "30px";
  panel.style.background = "rgba(10,20,40,0.92)";
  panel.style.padding = "14px 18px";
  panel.style.borderRadius = "18px";
  panel.style.color = "white";
  panel.style.zIndex = "999999";
  panel.style.boxShadow = "0 0 20px rgba(0,255,255,.5)";
  panel.style.fontFamily = "Arial";

  panel.innerHTML = `
    <div style="font-weight:bold;margin-bottom:8px">
      ⚛ QBioForge
    </div>

    <button id="scanBtn"
      style="background:#22d3ee;color:black;
      padding:8px 16px;border-radius:20px;
      font-weight:bold;border:none;width:100%;">
      Scan Video
    </button>

    <div id="status"
      style="margin-top:6px;font-size:12px;color:#aaa">
    </div>
  `;

  document.body.appendChild(panel);

  const btn = document.getElementById("scanBtn");
  const status = document.getElementById("status");

  btn.onclick = async () => {

    btn.disabled = true;
    status.innerText = "Capturing frames...";

    const frames = await captureFrames(video);

    status.innerText = "Sending to quantum engine...";

    chrome.runtime.sendMessage(
      {
        type: "FRAME_SCAN",
        frames: frames
      },
      function (response) {

        btn.disabled = false;

        if (!response || !response.success) {
          status.innerText = "Scan failed";
          return;
        }

        const r = response.data;

        status.innerHTML =
          (r.verdict === "REAL" ? "✔ REAL VIDEO" : "❌ DEEPFAKE") +
          "<br>" +
          "Confidence: " + Math.round(r.confidence * 100) + "%" +
          "<br>" +
          r.reason;
      }
    );
  };
}

async function captureFrames(video) {

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const frames = [];

  for (let i = 0; i < 10; i++) {

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const data = canvas.toDataURL("image/jpeg", 0.7);
    frames.push(data);

    await new Promise(r => setTimeout(r, 1000));
  }

  return frames;
}

setTimeout(waitForPlayer, 3000);
