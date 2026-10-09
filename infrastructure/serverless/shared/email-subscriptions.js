// NOTIFICATION_EMAILS="a@x.co,b@y.co" → the topic's EMAIL subscriptions.
// CloudFormation can't turn a comma-separated string into this list itself.
module.exports = () => {
  const emails = (process.env.NOTIFICATION_EMAILS || '')
    .split(',')
    .map((email) => email.trim())
    .filter(Boolean)

  if (emails.length === 0) {
    throw new Error(
      'NOTIFICATION_EMAILS is empty: set the comma-separated emails that ' +
        'receive the MLOps notifications.'
    )
  }

  return emails.map((address) => ({
    Protocol: 'email',
    Endpoint: address,
  }))
}
