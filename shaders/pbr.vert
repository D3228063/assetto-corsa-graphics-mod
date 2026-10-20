#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;
layout(location = 3) in vec4 aTangent;

uniform mat4 uModel;
uniform mat4 uViewProjection;
uniform mat4 uLightViewProjection;

out vec3 vWorldPosition;
out vec2 vTexCoord;
out mat3 vTBN;
out vec4 vLightPosition;

void main() {
    vec4 worldPosition = uModel * vec4(aPosition, 1.0);
    mat3 normalMatrix = transpose(inverse(mat3(uModel)));
    vec3 normal = normalize(normalMatrix * aNormal);
    vec3 tangent = normalize(normalMatrix * aTangent.xyz);
    tangent = normalize(tangent - normal * dot(normal, tangent));
    vec3 bitangent = normalize(cross(normal, tangent)) * aTangent.w;

    vWorldPosition = worldPosition.xyz;
    vTexCoord = aTexCoord;
    vTBN = mat3(tangent, bitangent, normal);
    vLightPosition = uLightViewProjection * worldPosition;
    gl_Position = uViewProjection * worldPosition;
}
