/*
   TV Modern Remaster Shader (Ultra-Fast Mali-400 Edition)
   Single-pass vivid color remaster, 3-tap horizontal selective dither blending,
   sharp-bilinear scaling and lightweight zero-cost scanlines.
   Calibrated for solid 60 fps on the Mali-400 MP2 (Allwinner A33 / R36S).

   - Selective 3-tap horizontal dither blend: restores 100% transparency (Sonic water,
     Streets of Rage 2 lights and shadows) while keeping character outlines, HUD and text sharp.
   - Ultra-lightweight screen scanline: alternating physical 480p line modulation without
     expensive exp/trig calls and with zero moire or intervals.
   - Fast color remaster: luma contrast and selective vibrance without heavy divisions.
*/

#pragma parameter DITHER_BLEND "DITHER BLEND (0=Off)" 1.00 0.0 1.0 0.05
#pragma parameter TV_SCANLINES "TV SCANLINES (0=Off)" 0.10 0.0 0.50 0.02
#pragma parameter PIXEL_SOFTNESS "PIXEL SOFTNESS" 0.10 0.0 1.0 0.05
#pragma parameter VIBRANCE "VIBRANCE" 0.40 0.0 1.0 0.05
#pragma parameter SATURATION "SATURATION" 1.08 0.5 1.3 0.01
#pragma parameter CONTRAST "S-CURVE Contrast" 0.25 0.0 1.0 0.05
#pragma parameter ROLLOFF "HIGHLIGHT ROLLOFF" 0.35 0.0 1.0 0.05
#pragma parameter BRIGHTNESS "BRIGHTNESS" 0.0 -0.30 0.30 0.01

#if defined(VERTEX)

#if __VERSION__ >= 130
#define COMPAT_VARYING out
#define COMPAT_ATTRIBUTE in
#define COMPAT_TEXTURE texture
#else
#define COMPAT_VARYING varying
#define COMPAT_ATTRIBUTE attribute
#define COMPAT_TEXTURE texture2D
#endif

COMPAT_ATTRIBUTE vec4 VertexCoord;
COMPAT_ATTRIBUTE vec4 COLOR;
COMPAT_ATTRIBUTE vec4 TexCoord;
COMPAT_VARYING vec4 COL0;
COMPAT_VARYING vec4 TEX0;

uniform mat4 MVPMatrix;
uniform int FrameDirection;
uniform int FrameCount;
uniform vec2 OutputSize;
uniform vec2 TextureSize;
uniform vec2 InputSize;

void main()
{
   gl_Position = MVPMatrix * VertexCoord;
   COL0 = COLOR;
   TEX0.xy = TexCoord.xy;
}

#elif defined(FRAGMENT)

#if __VERSION__ >= 130
#define COMPAT_VARYING in
#define COMPAT_TEXTURE texture
out vec4 FragColor;
#else
#define COMPAT_VARYING varying
#define COMPAT_TEXTURE texture2D
#define FragColor gl_FragColor
#endif

#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
#endif

COMPAT_VARYING vec4 COL0;
COMPAT_VARYING vec4 TEX0;

uniform sampler2D Texture;
uniform COMPAT_PRECISION vec2 OutputSize;
uniform COMPAT_PRECISION vec2 TextureSize;
uniform COMPAT_PRECISION vec2 InputSize;
uniform int FrameDirection;
uniform int FrameCount;

#ifdef PARAMETER_UNIFORM
uniform COMPAT_PRECISION float DITHER_BLEND;
uniform COMPAT_PRECISION float TV_SCANLINES;
uniform COMPAT_PRECISION float PIXEL_SOFTNESS;
uniform COMPAT_PRECISION float VIBRANCE;
uniform COMPAT_PRECISION float SATURATION;
uniform COMPAT_PRECISION float CONTRAST;
uniform COMPAT_PRECISION float ROLLOFF;
uniform COMPAT_PRECISION float BRIGHTNESS;
#else
#define DITHER_BLEND 1.00
#define TV_SCANLINES 0.10
#define PIXEL_SOFTNESS 0.10
#define VIBRANCE 0.40
#define SATURATION 1.08
#define CONTRAST 0.25
#define ROLLOFF 0.35
#define BRIGHTNESS 0.0
#endif

void main()
{
	// 1. Sharp-bilinear ultra-rapido
	COMPAT_PRECISION float px = InputSize.x / OutputSize.x;
	COMPAT_PRECISION float width = max(mix(px, 1.0, PIXEL_SOFTNESS), 0.0001);

	COMPAT_PRECISION vec2 p = TEX0.xy * TextureSize - 0.5;
	COMPAT_PRECISION vec2 i = floor(p);
	COMPAT_PRECISION vec2 f = clamp((fract(p) - 0.5) / width + 0.5, 0.0, 1.0);

	COMPAT_PRECISION vec2 uv = (i + 0.5 + f) / TextureSize;

	// 2. Dither blend horizontal seletivo (3 leituras) ultra-otimizado sem divisao
	COMPAT_PRECISION float dx = 1.0 / TextureSize.x;
	vec4 C_tex = COMPAT_TEXTURE(Texture, uv);
	vec4 L_tex = COMPAT_TEXTURE(Texture, uv - vec2(dx, 0.0));
	vec4 R_tex = COMPAT_TEXTURE(Texture, uv + vec2(dx, 0.0));

	COMPAT_PRECISION vec3 C = C_tex.rgb;
	COMPAT_PRECISION vec3 L = L_tex.rgb;
	COMPAT_PRECISION vec3 R = R_tex.rgb;

	COMPAT_PRECISION float diff_LR = dot(abs(L - R), vec3(0.3333333));
	COMPAT_PRECISION float diff_C = dot(abs(C - 0.5 * (L + R)), vec3(0.3333333));

	// Rampa rapida: funde 100% de dither (agua/luz) e anula em contornos solidos (diff_C <= 0.5 * diff_LR)
	COMPAT_PRECISION float w_dither = clamp((diff_C - 0.5 * diff_LR) * 10.0, 0.0, 1.0) * DITHER_BLEND;
	COMPAT_PRECISION vec3 c = mix(C, 0.5 * C + 0.25 * (L + R), w_dither);

	// 3. Cor viva remaster ultra-leve (zero divisoes, preserva 0.0 e 1.0 exatamente)
	COMPAT_PRECISION float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
	COMPAT_PRECISION float sat = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));

	// Vibrance seletiva com amortecimento parabolico (impede clipping de saturação)
	COMPAT_PRECISION float sat_boost = VIBRANCE * (1.0 - sat) + (SATURATION - 1.0);
	c += (c - luma) * (c * (1.0 - c) * 4.0) * sat_boost;

	// Curva em S polinomial com compensacao de brilho integrada (preserva pretos e brancos)
	c += c * (1.0 - c) * ((c - 0.35) * CONTRAST + BRIGHTNESS);

	// 4. Scanline milimetrica na grade da tela 480p (1 instrucao mod: perfeitamente uniforme, zero moire)
	#if defined(GL_ES)
	COMPAT_PRECISION float scan = mod(floor(gl_FragCoord.y), 2.0);
	#else
	COMPAT_PRECISION float scan = mod(floor(TEX0.y * OutputSize.y), 2.0);
	#endif
	c *= (1.0 - TV_SCANLINES * scan);

	FragColor = vec4(clamp(c, 0.0, 1.0), C_tex.a);
}

#endif
