// Deployment contract guard: the endpoint can only be built from a model
// package a person approved. OnModelApproved writes these SSM parameters on
// approval; until then they hold the placeholder "none", which CloudFormation
// would reject with an unhelpful validation error. Fail early instead.
const PREFIX = '/data-science-customer-churn-pipeline'

const approved =
  (name, isValid) =>
  async ({ resolveVariable }) => {
    const value = await resolveVariable(`ssm:${PREFIX}/${name}`)
    if (!isValid(String(value))) {
      throw new Error(
        `No approved model yet (${PREFIX}/${name} = "${value}"). Approve a ` +
          'model version first: npm run models -- --approve <version>'
      )
    }
    return value
  }

module.exports.packageArn = approved('ApprovedModelPackageArn', (value) =>
  value.startsWith('arn:')
)
module.exports.baselineConstraintsUri = approved(
  'ApprovedBaselineConstraintsUri',
  (value) => value.startsWith('s3://')
)
module.exports.baselineStatisticsUri = approved(
  'ApprovedBaselineStatisticsUri',
  (value) => value.startsWith('s3://')
)
