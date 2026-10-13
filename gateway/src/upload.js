import multer from "multer";
import { UPLOAD_DIR } from "./config.js";

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const safe = file.originalname.replace(/[^\w.\-]/g, "_");
    cb(null, `${Date.now()}_${safe}`);
  },
});

export const upload = multer({
  storage,
  limits: { fileSize: 2 * 1024 * 1024 * 1024 }, // 2 GB per file
  fileFilter: (req, file, cb) => {
    const ok = /\.(tif|tiff)$/i.test(file.originalname);
    if (ok) return cb(null, true);
    const e = new Error("only .tif / .tiff GeoTIFF files are allowed");
    e.status = 400;
    cb(e, false);
  },
}).array("images", 2);