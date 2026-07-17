chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

  if (request.type === "FRAME_SCAN") {

    fetch("http://localhost:5000/api/frame_scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        frames: request.frames
      })
    })
    .then(res => res.json())
    .then(data => {
      sendResponse({ success: true, data: data });
    })
    .catch(err => {
      sendResponse({ success: false, error: err.toString() });
    });

    return true;
  }

});
