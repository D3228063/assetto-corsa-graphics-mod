#version 300 es
precision highp float;

in vec3 vWorldPosition;
in vec2 vTexCoord;
in mat3 vTBN;
in vec4 vLightPosition;

layout(location = 0) out vec4 fragColor;

uniform sampler2D uAlbedoMap;
uniform sampler2D uNormalMap;
uniform sampler2D uMetallicRoughnessMap;
uniform sampler2D uOcclusionMap;
uniform sampler2DShadow uShadowMap;
uniform samplerCube uEnvironmentMap;
uniform vec3 uCameraPosition;
uniform vec3 uLightDirection;
uniform vec3 uLightColor;
uniform vec3 uAmbientColor;
uniform float uShadowBias;

const float PI = 3.14159265359;

float distributionGGX(vec3 n, vec3 h, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float nDotH = max(dot(n, h), 0.0);
    float nDotH2 = nDotH * nDotH;
    float denominator = nDotH2 * (a2 - 1.0) + 1.0;
    return a2 / max(PI * denominator * denominator, 0.0001);
}

float geometrySchlickGGX(float nDotV, float roughness) {
    float r = roughness + 1.0;
    float k = r * r / 8.0;
    return nDotV / max(nDotV * (1.0 - k) + k, 0.0001);
}

float shadowVisibility(vec3 normal) {
    vec3 projected = vLightPosition.xyz / vLightPosition.w;
    projected = projected * 0.5 + 0.5;
    if (projected.z <= 0.0 || projected.z >= 1.0 ||
        any(lessThan(projected.xy, vec2(0.0))) ||
        any(greaterThan(projected.xy, vec2(1.0)))) {
        return 1.0;
    }

    vec2 texel = 1.0 / vec2(textureSize(uShadowMap, 0));
    float bias = max(uShadowBias * (1.0 - max(dot(normal, normalize(-uLightDirection)), 0.0)), uShadowBias * 0.25);
    float visibility = 0.0;
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            visibility += texture(uShadowMap, vec3(projected.xy + vec2(float(x), float(y)) * texel, projected.z - bias));
        }
    }
    return visibility / 9.0;
}

void main() {
    vec4 albedoSample = texture(uAlbedoMap, vTexCoord);
    vec3 albedo = pow(max(albedoSample.rgb, vec3(0.0)), vec3(2.2));
    vec3 normal = normalize(vTBN * (texture(uNormalMap, vTexCoord).xyz * 2.0 - 1.0));
    vec2 material = texture(uMetallicRoughnessMap, vTexCoord).gb;
    float roughness = clamp(material.x, 0.045, 1.0);
    float metallic = clamp(material.y, 0.0, 1.0);
    float occlusion = texture(uOcclusionMap, vTexCoord).r;

    vec3 viewDirection = normalize(uCameraPosition - vWorldPosition);
    vec3 lightDirection = normalize(-uLightDirection);
    vec3 halfway = normalize(viewDirection + lightDirection);
    float nDotL = max(dot(normal, lightDirection), 0.0);
    float nDotV = max(dot(normal, viewDirection), 0.0);
    vec3 f0 = mix(vec3(0.04), albedo, metallic);
    vec3 fresnel = f0 + (1.0 - f0) * pow(1.0 - max(dot(halfway, viewDirection), 0.0), 5.0);
    float distribution = distributionGGX(normal, halfway, roughness);
    float geometry = geometrySchlickGGX(nDotV, roughness) * geometrySchlickGGX(nDotL, roughness);
    vec3 specular = distribution * geometry * fresnel / max(4.0 * nDotV * nDotL, 0.001);
    vec3 diffuseWeight = (vec3(1.0) - fresnel) * (1.0 - metallic);
    float visibility = shadowVisibility(normal);

    vec3 direct = (diffuseWeight * albedo / PI + specular) * uLightColor * nDotL * visibility;
    vec3 reflectionDirection = reflect(-viewDirection, normal);
    vec3 environment = texture(uEnvironmentMap, reflectionDirection).rgb * fresnel;
    vec3 ambient = (uAmbientColor * albedo * diffuseWeight + environment) * occlusion;
    vec3 color = max(direct + ambient, vec3(0.0));
    fragColor = vec4(color, albedoSample.a);
}
