#!/usr/bin/env python3
"""Build an independent USB photo importer in a caller-selected temporary directory.

No device installation or photo permissions are changed by this script.
All sources and resources are included in this standalone repository.
"""
import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--platform', choices=['device', 'simulator'], required=True)
parser.add_argument('--team', help='Existing Apple development team, for device builds')
parser.add_argument('--build', type=int, default=1)
parser.add_argument('--bundle-id', default='io.github.mosigin.wangtu-photo-transfer')
parser.add_argument('--allow-provisioning-updates', action='store_true')
parser.add_argument('--compile', action='store_true', help='Build only after explicit device-build authorization')
args = parser.parse_args()
if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', args.bundle_id):
    parser.error('Invalid bundle identifier')
if args.compile and sys.platform != 'darwin':
    parser.error('Xcode builds require macOS; Windows USB transfer is not implemented')
if args.build < 1:
    parser.error('--build must be positive')
if args.platform == 'device' and not args.team:
    parser.error('Device builds require --team')
source = Path(__file__).resolve().parents[1] / "ios"
output = args.output.resolve()
if output == source or source in output.parents:
    parser.error('Use a separate temporary output directory')
output.mkdir(parents=True, exist_ok=True)
project = output / 'WangtuPhotoTransfer.xcodeproj'
project.mkdir(exist_ok=True)
for name in ['WangtuPhotoTransfer.swift', 'ImportPolicy.swift']:
    shutil.copy2(source / name, output / name)
info = {
    'CFBundleIdentifier': '$(PRODUCT_BUNDLE_IDENTIFIER)',
    'CFBundleExecutable': '$(EXECUTABLE_NAME)',
    'CFBundleName': 'WangtuPhotoTransfer',
    'CFBundleDisplayName': 'Wangtu Photo Transfer',
    'CFBundlePackageType': 'APPL',
    'CFBundleShortVersionString': '1.0',
    'CFBundleVersion': str(args.build),
    'LSRequiresIPhoneOS': True,
    'NSPhotoLibraryUsageDescription': 'Adds selected photos and videos over USB and verifies originals locally. Does not delete existing media or transfer over the network.',
    'UILaunchScreen': {},
    'NSPhotoLibraryAddUsageDescription': 'Adds selected photos and videos to your photo library.',
    'UIApplicationSceneManifest': {'UIApplicationSupportsMultipleScenes': False},
    'UISupportedInterfaceOrientations': ['UIInterfaceOrientationPortrait'],
}
(output / 'Info.plist').write_bytes(plistlib.dumps(info))

shutil.copytree(source / 'Assets.xcassets', output / 'Assets.xcassets', dirs_exist_ok=True)
# A standalone project generated without modifying any other app.
def uid(n): return f'{n:024X}'
objects = {}
def obj(n, isa, **kw): objects[uid(n)] = dict(isa=isa, **kw)
obj(1, 'PBXProject', attributes={'LastUpgradeCheck': '2700'}, buildConfigurationList=uid(20),
    compatibilityVersion='Xcode 14.0', developmentRegion='en', knownRegions=['en', 'zh-Hans'],
    mainGroup=uid(2), productRefGroup=uid(3), projectDirPath='', projectRoot='', targets=[uid(4)])
obj(2, 'PBXGroup', children=[uid(5), uid(6), uid(7), uid(34), uid(9), uid(3)], sourceTree='<group>')
obj(3, 'PBXGroup', children=[uid(8)], name='Products', sourceTree='<group>')
obj(4, 'PBXNativeTarget', buildConfigurationList=uid(21), buildPhases=[uid(10), uid(11), uid(12)],
    buildRules=[], dependencies=[], name='WangtuPhotoTransfer', productName='WangtuPhotoTransfer',
    productReference=uid(8), productType='com.apple.product-type.application')
for n, path, filetype in [(5, 'WangtuPhotoTransfer.swift', 'sourcecode.swift'),
                         (6, 'ImportPolicy.swift', 'sourcecode.swift'),
                         (7, 'Localizable.strings', 'text.plist.strings')]:
    obj(n, 'PBXFileReference', lastKnownFileType=filetype, path=path, sourceTree='<group>')
obj(7, 'PBXVariantGroup', children=[uid(30), uid(31)], name='Localizable.strings', sourceTree='<group>')
obj(34, 'PBXVariantGroup', children=[uid(32), uid(33)], name='InfoPlist.strings', sourceTree='<group>')
for n, lang, name in [(30, 'en', 'Localizable'), (31, 'zh-Hans', 'Localizable'),
                      (32, 'en', 'InfoPlist'), (33, 'zh-Hans', 'InfoPlist')]:
    obj(n, 'PBXFileReference', lastKnownFileType='text.plist.strings', name=lang,
        path=f'Resources/{lang}.lproj/{name}.strings', sourceTree='<group>')
obj(35, 'PBXBuildFile', fileRef=uid(34))
obj(9, 'PBXFileReference', lastKnownFileType='folder.assetcatalog', path='Assets.xcassets', sourceTree='<group>')
obj(19, 'PBXBuildFile', fileRef=uid(9))
obj(8, 'PBXFileReference', explicitFileType='wrapper.application', path='WangtuPhotoTransfer.app',
    includeInIndex=0, sourceTree='BUILT_PRODUCTS_DIR')
obj(10, 'PBXSourcesBuildPhase', buildActionMask=2147483647, files=[uid(15), uid(16)], runOnlyForDeploymentPostprocessing=0)
obj(11, 'PBXFrameworksBuildPhase', buildActionMask=2147483647, files=[], runOnlyForDeploymentPostprocessing=0)
obj(12, 'PBXResourcesBuildPhase', buildActionMask=2147483647, files=[uid(17), uid(35), uid(19)], runOnlyForDeploymentPostprocessing=0)
for n in [5, 6, 7]: obj(n+10, 'PBXBuildFile', fileRef=uid(n))
for n, config in [(20, 22), (21, 23)]:
    obj(n, 'XCConfigurationList', buildConfigurations=[uid(config)], defaultConfigurationIsVisible=0, defaultConfigurationName='Debug')
obj(22, 'XCBuildConfiguration', name='Debug', buildSettings={
    'CLANG_ENABLE_MODULES': 'YES', 'SWIFT_VERSION': '5.0',
    'IPHONEOS_DEPLOYMENT_TARGET': '17.0', 'SDKROOT': 'iphoneos',
    'SWIFT_OPTIMIZATION_LEVEL': '-Onone', 'DEBUG_INFORMATION_FORMAT': 'dwarf-with-dsym',
})
settings = {
    'PRODUCT_NAME': 'WangtuPhotoTransfer',
    'PRODUCT_BUNDLE_IDENTIFIER': args.bundle_id,
    'INFOPLIST_FILE': 'Info.plist', 'TARGETED_DEVICE_FAMILY': '1',
    'CODE_SIGN_STYLE': 'Automatic', 'ENABLE_DEBUG_DYLIB': 'NO',
    'ASSETCATALOG_COMPILER_APPICON_NAME': 'AppIcon', 'SWIFT_EMIT_LOC_STRINGS': 'NO', 'LD_RUNPATH_SEARCH_PATHS': ['$(inherited)', '@executable_path/Frameworks'],
}
if args.team: settings['DEVELOPMENT_TEAM'] = args.team
obj(23, 'XCBuildConfiguration', name='Debug', buildSettings=settings)
# Xcode accepts its property-list project representation in XML form.
(project / 'project.pbxproj').write_bytes(plistlib.dumps({
    'archiveVersion': '1', 'classes': {}, 'objectVersion': '56',
    'objects': objects, 'rootObject': uid(1),
}, sort_keys=False))
platform = 'iOS' if args.platform == 'device' else 'iOS Simulator'
command = ['xcrun', 'xcodebuild', '-project', str(project), '-scheme', 'WangtuPhotoTransfer',
           '-configuration', 'Debug', '-destination', 'generic/platform=' + platform,
           '-derivedDataPath', str(output / 'DerivedData'), 'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=YES']
if args.platform == 'simulator': command.append('CODE_SIGNING_ALLOWED=NO')
if args.allow_provisioning_updates: command.append('-allowProvisioningUpdates')
command.append('build')
# Generate this helper's resources from the sole shared catalog sources.
root = source.parent
ui = json.loads((source / 'Localizable.xcstrings').read_text())['strings']
identity = json.loads((source / 'InfoPlist.xcstrings').read_text())['strings']
keys = list(ui)
for language in ['en', 'zh-Hans']:
    resources = output / 'Resources' / (language + '.lproj')
    resources.mkdir(parents=True, exist_ok=True)
    def strings(mapping):
        return '\n'.join(json.dumps(k, ensure_ascii=False) + ' = ' + json.dumps(v, ensure_ascii=False) + ';'
                         for k, v in mapping.items()) + '\n'
    translations = {k: ui[k]['localizations'][language]['stringUnit']['value'] for k in keys}
    (resources / 'Localizable.strings').write_text(strings(translations))
    fields = {'CFBundleDisplayName': '妄图照片直传',
              'NSPhotoLibraryUsageDescription': '通过 USB 添加你选择的照片和视频，并在本机读回核验。不删除已有媒体，不通过网络传输。',
              'NSPhotoLibraryAddUsageDescription': '通过 USB 添加你选择的照片和视频，并在本机读回核验。不删除已有媒体，不通过网络传输。'}
    fields = {key: identity[value]['localizations'][language]['stringUnit']['value'] for key, value in fields.items()}
    (resources / 'InfoPlist.strings').write_text(strings(fields))
if not args.compile:
    print(json.dumps({'prepared': str(project), 'compiled': False, 'bundle': settings['PRODUCT_BUNDLE_IDENTIFIER']}))
    raise SystemExit(0)
result = subprocess.run(command, cwd=output)
raise SystemExit(result.returncode)
