import axios from "axios";
import { ML_URL } from "./config.js";

const http = axios.create({ baseURL: ML_URL, timeout: 15 * 60 * 1000 });

export async function mlGet(p) {
  return (await http.get(p)).data;
}

export async function mlPost(p, body) {
  return (await http.post(p, body)).data;
}