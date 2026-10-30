import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const workspaceDir='C:/Users/uuuwk/karissa/OPT1/OPT1';
const skill='C:/Users/uuuwk/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const staging=workspaceDir+'/.build/opt1_presentation_v3';
const source='C:/Users/uuuwk/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Roaming/Codex/web/Codex/artifact-sessions/exports/latest/2351fc6dcbcb45e09ad493f30d9e20e9fe26b7039fe4904f0367bd03f5753765/opt1_candidate_v3.pptx';
await fs.mkdir(workspaceDir+'/output/presentations',{recursive:true});
await fs.copyFile(source,staging+'/candidate.pptx');
const tables=[3,4,6,10,15,17,18,20,21,25,26,27,28,29,30,37];
const result=await finalizePresentation({
 workspaceDir,candidatePath:staging+'/candidate.pptx',
 finalPath:workspaceDir+'/output/presentations/OPT1_教授報告_完整引用版_v3.pptx',
 pythonExecutable:'C:/Users/uuuwk/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:[19],
 fontPolicy:{basis:'reference',families:['Microsoft JhengHei'],referencePath:workspaceDir+'/output/presentations/OPT1_研究主軸與執行邏輯_口語版_v2.pptx',referenceSha256:'7ddd52699f9c845b0312810d9fe331f08d35be46f270cd09a221c49a1681f37b'},
 materializeLiteralChartWorkbooks:false,nativeChartTargetApplication:'powerpoint',
 verifyArtifactToolImport:true,receiptPath:staging+'/validation.json'
});
console.log(JSON.stringify({path:result.finalPath,sha256:result.finalSha256,slideCount:result.packageIntegrity.slide_count,package:result.packageIntegrity.status,layoutFindings:result.presentationLayout.finding_count,import:result.firstPartyImport.passed,chart:result.nativeChartValidation.passed},null,2));
