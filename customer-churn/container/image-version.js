// Immutable model images: the tag is a hash of everything baked into the
// image (Dockerfile, entrypoint, pinned requirements and the model packages
// of src/). Every model
// package points to the exact image that trained it, and the ECR repository
// rejects overwriting a tag.
//
// As a Serverless `${file()}` resolver it also checks the tag exists in ECR,
// so a pipeline is never deployed pointing to an image that wasn't pushed
// (`npm run image:push`). SKIP_IMAGE_CHECK=true skips that check.
const crypto = require('crypto')
const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')

const PROJECT_DIR = path.resolve(__dirname, '..')
// Packages copied into the image (keep in sync with container/Dockerfile).
const IMAGE_PACKAGES = [
  'features',
  'models',
  'monitoring',
  'pipelines',
  'serving',
]
// build-push.sh is included because it decides the manifest format SageMaker
// receives: changing how the image is built must produce a new tag.
const IMAGE_FILES = [
  'container/Dockerfile',
  'container/entrypoint.sh',
  'container/requirements.txt',
  'container/build-push.sh',
]

const imageVersion = () => {
  const packageFiles = IMAGE_PACKAGES.flatMap((name) =>
    fs
      .readdirSync(path.join(PROJECT_DIR, 'src', name), { recursive: true })
      .filter((file) => file.endsWith('.py'))
      .map((file) => path.join('src', name, file))
  ).sort()
  const hash = crypto.createHash('sha256')
  for (const file of [...IMAGE_FILES, 'src/__init__.py', ...packageFiles]) {
    hash.update(file)
    hash.update(fs.readFileSync(path.join(PROJECT_DIR, file)))
  }
  return hash.digest('hex').slice(0, 12)
}

const assertPushed = (repositoryName, tag) => {
  try {
    execFileSync(
      'aws',
      [
        'ecr',
        'describe-images',
        '--repository-name',
        repositoryName,
        '--image-ids',
        `imageTag=${tag}`,
      ],
      { stdio: 'ignore' }
    )
  } catch {
    throw new Error(
      `Image ${repositoryName}:${tag} is not in ECR. ` +
        'Run `npm run image:push` before deploying.'
    )
  }
}

module.exports = async ({ resolveVariable }) => {
  const tag = imageVersion()
  if (process.env.SKIP_IMAGE_CHECK !== 'true') {
    assertPushed(await resolveVariable('self:custom.image.repositoryName'), tag)
  }
  return tag
}
module.exports.imageVersion = imageVersion
