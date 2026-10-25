/*
   GBA Modern Remaster Shader
   Single-pass color remastering and anti-aliased soft-edge scaling for Game Boy Advance.
   Optimized for mobile GPUs (Mali-G31 / OpenGL ES) and modern displays.

   - Restores natural, balanced colors on modern displays (R36S, IPS, OLED).
   - Eliminates pixel shimmering on non-integer scaling without blurring the image.
   - Ultra-lightweight single-pass pipeline for solid 60 FPS lock.
*/

#pragma parameter CORRECTION_STRENGTH "Color Correction Strength" 1.0 0.0 1.0 0.05
#pragma parameter SATURATION "Color Saturation" 1.0 0.0 2.0 0.05
#pragma parameter GAMMA_BOOST "Luminance / Gamma Boost" 1.0 0.8 1.4 0.02
#pragma parameter PIXEL_SOFTNESS "Pixel Softness (0=Sharp, 1=Soft)" 0.35 0.0 1.0 0.05

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
uniform COMPAT_PRECISION float CORRECTION_STRENGTH;
uniform COMPAT_PRECISION float SATURATION;
uniform COMPAT_PRECISION float GAMMA_BOOST;
uniform COMPAT_PRECISION float PIXEL_SOFTNESS;
#else
#define CORRECTION_STRENGTH 1.0
#define SATURATION 1.0
#define GAMMA_BOOST 1.0
#define PIXEL_SOFTNESS 0.35
#endif

void main()
{
	// 1. Coordinate anti-aliased soft-edge scaling (adaptive Quilez smoothstep)
	COMPAT_PRECISION vec2 p = TEX0.xy * TextureSize - 0.5;
	COMPAT_PRECISION vec2 i = floor(p);
	COMPAT_PRECISION vec2 f = fract(p);

	// Half-width transition zone clamped to avoid division by zero or over-smoothing
	COMPAT_PRECISION float s = clamp(PIXEL_SOFTNESS * 0.5, 0.0001, 0.5);
	COMPAT_PRECISION vec2 f_warped = smoothstep(vec2(0.5 - s), vec2(0.5 + s), f);
	COMPAT_PRECISION vec2 sampleCoord = (i + 0.5 + f_warped) / TextureSize;

	vec4 texel = COMPAT_TEXTURE(Texture, sampleCoord);
	COMPAT_PRECISION vec3 rawColor = texel.rgb;

	// 2. Linearize gamma (2.2)
	COMPAT_PRECISION vec3 linearColor = pow(max(rawColor, vec3(0.0)), vec3(2.2));

	// 3. Modern GBA Color Calibration Matrix
	// Balances fluorescent greens and burning reds to sRGB D65 white point while preserving 100% luminance
	const mat3 GBA_Matrix = mat3(
		vec3(0.82, 0.09, 0.05), // Column 0: contributions from input Red
		vec3(0.14, 0.76, 0.15), // Column 1: contributions from input Green
		vec3(0.04, 0.15, 0.80)  // Column 2: contributions from input Blue
	);

	COMPAT_PRECISION vec3 corrected = GBA_Matrix * linearColor;

	// 4. Gamma restoration with adjustable luminance/gamma boost
	COMPAT_PRECISION float invGamma = 1.0 / (2.2 * GAMMA_BOOST);
	COMPAT_PRECISION vec3 reencoded = pow(max(corrected, vec3(0.0)), vec3(invGamma));

	// 5. Saturation fine-tuning using standard Rec. 709 luma weights
	COMPAT_PRECISION float luma = dot(reencoded, vec3(0.2126, 0.7152, 0.0722));
	COMPAT_PRECISION vec3 saturated = mix(vec3(luma), reencoded, SATURATION);

	// 6. Blend between raw input and calibrated output
	COMPAT_PRECISION vec3 finalColor = mix(rawColor, saturated, CORRECTION_STRENGTH);

	FragColor = vec4(clamp(finalColor, 0.0, 1.0), texel.a);
}

#endif
