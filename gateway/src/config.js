import "dotenv/config";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");

export const PORT = Number(process.env.PORT || 4000);
export const ML_URL = process.env.ML_URL || "http://127.0.0.1:8000";
export const UPLOAD_DIR = path.resolve(ROOT, "data/uploads");
export const OUTPUTS_DIR = path.resolve(ROOT, "outputs");