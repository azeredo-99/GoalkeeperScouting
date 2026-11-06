import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setConcurrency(2);
// No teu computador o Remotion descarrega o browser sozinho.
// Num ambiente sem acesso a essa transferência, aponta para um Chrome headless já instalado:
if (process.env.REMOTION_BROWSER) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
}
