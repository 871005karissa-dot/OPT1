import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const workspaceDir='C:/Users/uuuwk/karissa/OPT1/OPT1';
const skill='C:/Users/uuuwk/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const staging=workspaceDir+'/.build/opt1_presentation_v2';
const source='C:/Users/uuuwk/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Roaming/Codex/web/Codex/artifact-sessions/exports/latest/2351fc6dcbcb45e09ad493f30d9e20e9fe26b7039fe4904f0367bd03f5753765/opt1_candidate_v2.pptx';
await fs.mkdir(workspaceDir+'/output/presentations',{recursive:true});
await fs.copyFile(source,staging+'/candidate.pptx');
const tables=[3,4,6,10,15,17,18,20,21,25,26];
const result=await finalizePresentation({
 workspaceDir,candidatePath:staging+'/candidate.pptx',
 finalPath:workspaceDir+'/output/presentations/OPT1_研究主軸與執行邏輯_口語版_v2.pptx',
 pythonExecutable:'C:/Users/uuuwk/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:[19],
 fontPolicy:{basis:'design',families:['Microsoft JhengHei']},
 materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',
 verifyArtifactToolImport:true,receiptPath:staging+'/validation.json'
});
console.log(JSON.stringify(result,null,2));
