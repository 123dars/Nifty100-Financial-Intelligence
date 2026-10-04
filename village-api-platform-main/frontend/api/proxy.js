export default async function handler(req, res) {
  const backendBase = process.env.VILLAGE_API_BASE_URL;
  const apiKey = process.env.VILLAGE_API_KEY;
  const apiSecret = process.env.VILLAGE_API_SECRET;

  if (!backendBase || !apiKey || !apiSecret) {
    return res.status(500).json({
      error: "Production API proxy is not configured.",
    });
  }

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  try {
    const incomingUrl = new URL(
      req.url,
      `https://${req.headers.host}`
    );

    const proxyPrefix = "/api/proxy/";
    let path = incomingUrl.pathname;

    if (path.startsWith(proxyPrefix)) {
      path = path.slice(proxyPrefix.length);
    }

    path = path.replace(/^\/+/, "");

    const target = new URL(
      `${backendBase.replace(/\/+$/, "")}/${path}`
    );

    target.search = incomingUrl.search;

    const headers = {
      "X-API-Key": apiKey,
      "X-API-Secret": apiSecret,
      "Accept": "application/json",
    };

    if (req.headers.authorization) {
      headers.Authorization = req.headers.authorization;
    }

    if (req.headers["content-type"]) {
      headers["Content-Type"] = req.headers["content-type"];
    }

    const hasBody = !["GET", "HEAD"].includes(
      req.method || "GET"
    );

    const body = hasBody
      ? await readRequestBody(req)
      : undefined;

    const response = await fetch(target.toString(), {
      method: req.method || "GET",
      headers,
      body,
      redirect: "manual",
    });

    const contentType = response.headers.get("content-type");

    if (contentType) {
      res.setHeader("Content-Type", contentType);
    }

    const responseBody = Buffer.from(
      await response.arrayBuffer()
    );

    return res
      .status(response.status)
      .send(responseBody);
  } catch (error) {
    console.error("Village API proxy error:", error);

    return res.status(502).json({
      error: "Unable to reach the Village API backend.",
    });
  }
}

async function readRequestBody(req) {
  if (req.body && typeof req.body === "object") {
    return JSON.stringify(req.body);
  }

  const chunks = [];

  for await (const chunk of req) {
    chunks.push(
      Buffer.isBuffer(chunk)
        ? chunk
        : Buffer.from(chunk)
    );
  }

  return Buffer.concat(chunks);
}
