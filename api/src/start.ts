import { app } from "./server.js";
app.listen(Number(process.env.API_PORT || 3001), () => console.log("API sintética em http://localhost:3001"));
