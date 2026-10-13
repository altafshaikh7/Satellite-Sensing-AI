import express from "express";
import cors from "cors";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { PORT, UPLOAD_DIR, OUTPUTS_DIR } from "./config.js";
import router from "./routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const app = express();
app.use(cors());
app.use(express.json());
app.use("/api", router);
app.use("/outputs", express.static(OUTPUTS_DIR));
app.use(express.static(path.resolve(__dirname, "../public")));

app.use((err, req, res, next) => {
  if (err.code === "ECONNREFUSED") {
    return res.status(503).json({ error: "ML service not reachable. Start uvicorn on ML_URL." });
  }
  res.status(err.status || 500).json({ error: err.message });
});

app.listen(PORT, () => console.log(`Gateway running on http://127.0.0.1:${PORT}`));