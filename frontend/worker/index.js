/* Custom service worker code merged into next-pwa's generated sw.js.
 * Handles push notifications and click-to-open behavior.
 */

self.addEventListener("push", (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch (_err) {
    payload = { title: "Tlearning", body: event.data.text() };
  }
  const { title = "Tlearning", body = "", data = {} } = payload;
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      data,
      tag: data.artifact_id || "tlearning",
      requireInteraction: false,
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const url = data.artifact_id ? `/study/${data.artifact_id}` : "/dashboard";
  event.waitUntil(
    (async () => {
      // Best-effort click tracking before navigating
      if (data.log_id) {
        try {
          await fetch(`/api/v1/notifications/${data.log_id}/clicked`, {
            method: "POST",
            credentials: "include",
          });
        } catch (_e) {
          /* ignore — metric only */
        }
      }
      const clients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      for (const client of clients) {
        if (client.url.includes(url) && "focus" in client) {
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })(),
  );
});

// Background sync: when the browser regains connectivity, dispatch a message
// to any open client asking it to flush the IndexedDB-queued review answers.
// The actual flush runs in the page bundle (service workers can't easily share
// the IndexedDB helpers + fetch wrappers from the app bundle).
self.addEventListener("sync", (event) => {
  if (event.tag !== "flush-answers") return;
  event.waitUntil(
    (async () => {
      const clients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      for (const client of clients) {
        client.postMessage({ type: "flush-answers" });
      }
    })(),
  );
});
