import assert from "node:assert/strict";
import { test } from "node:test";
import { app } from "./server.js";
import { observations } from "./server.js";
test("dataset is synthetic and has ten rows", () => {
  assert.equal(observations.length, 10);
});
test("health endpoint responds", async () => {
  const server = app.listen(0);
  const address = server.address() as { port: number };
  const response = await fetch(`http://localhost:${address.port}/api/health`);
  assert.deepEqual(await response.json(), { status: "ok" });
  server.close();
});
