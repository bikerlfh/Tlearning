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
  const artifactId = event.notification.data && event.notification.data.artifact_id;
  const url = artifactId ? `/study/${artifactId}` : "/dashboard";
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        for (const client of clients) {
          if (client.url.includes(url) && "focus" in client) {
            return client.focus();
          }
        }
        return self.clients.openWindow(url);
      }),
  );
});
