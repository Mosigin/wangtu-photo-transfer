# 无文字应用图标

`logo.png` 为1024×1024不透明PNG，相同图像用于README与iOS AppIcon，外框由系统遮罩处理。

## 当前设计

2026-10-31按用户反馈重新设计为简洁的蓝色工具图标：左下电脑、右上手机、左上转向手机的箭头。浅蓝白底配清晰的蓝色轮廓，设备比例、圆角和线条尽量统一，箭头缩小，屏幕留白。

此前的白色厚框、纸纹、柔软投影、山景和大箭头产生了玩具／手工贴纸感；这些不是用户要的相册折叠风格。后续沿用浅蓝、清爽的工具方向，以清晰轮廓和小尺寸辨识为准，避免再叠加装饰性材质和重复图案。

## 验证

1024×1024、无透明通道、README与AppIcon内容一致；64和32像素缩略图已目视检查，电脑、手机、箭头仍可区分；6项工程／资源检查通过。本次未构建或安装手机App。

## 生成记录

使用内置 imagegen；上一版仅作为三元素布局的编辑参考，重新绘制轮廓与比例。输出仅进行标准尺寸准备。当前版本提示词：

> Use case: precise-object-edit / logo-brand. Completely redesign the referenced icon as a mature, precise, professional photo-transfer utility app mark. The reference is ONLY for the semantic layout: COMPUTER at lower left, PHONE at upper right, ARROW at upper left pointing toward the phone. Rebuild the shapes from scratch; do not preserve the old thick white frames, giant arrow, mountain pictures, paper texture, lighting or proportions. Art direction: clean flat vector-style geometry, exceptionally disciplined spacing, consistent optical stroke weight, restrained corner radii, calm light-blue family, strong small-size legibility. This should look like a polished serious desktop utility, not an illustration. Opaque square canvas 1024x1024 with a uniform very pale cool blue-white background (#F2F7FC). Main device outlines in a clear medium-deep blue around #2678C6; transfer arrow in a slightly brighter blue around #398DDA. Limit to these two blues and background. Layout: a simplified thin-profile laptop in the lower-left (roughly x18–59%, y48–77%), a smaller upright smartphone in the upper-right (roughly x65–83%, y21–56%), and a modest smooth right-angle bent arrow above the computer in the upper-left/top-middle (roughly x31–59%, y24–42%), arrow rising then turning right toward the phone. Preserve generous separation and carefully balance visual mass. Devices are front-view clean outline glyphs; laptop screen is a wide landscape rectangle with moderately rounded corners and a simple narrow horizontal base; phone is a slim portrait rectangle with a single short restrained top earpiece. Screens are completely empty negative space: NO sun, NO mountains, NO scenic imagery, NO app grid. All outline strokes optically uniform, about 25–30px at 1024px, not chunky, not hairline. Arrow stem similar in weight to device outlines, arrowhead small and restrained, no oversize swoosh. Clean construction, straight edges, crisp antialiasing, clear gap between all three elements. Absolutely FLAT artwork: zero paper grain, noise, shadows, bevels, extrusion, glowing edges, material textures, lighting, soft-focus or 3D. No pastel-on-pastel washed-out contrast. No playful bubbly shapes. No text, letters, numerals, watermarks, trademark, cable or hands. One coherent icon only. Full-bleed square opaque background, no outer rounded-square border, no pre-rounded canvas corners, no mockup and no multiple options.
