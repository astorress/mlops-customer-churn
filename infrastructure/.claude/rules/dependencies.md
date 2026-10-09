# Dependencies — infrastructure

## Library > Cloud Formation > Virtual Private Cloud (vendored)

- Repository from `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_REPOSITORY`, branch from
  `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME` (`sls-v4.x`).
- Cloned by `.docker/entrypoint.sh` into `customlib/cloud-formation/virtual-private-cloud` and built with its
  `dist.sh`; the distribution ships its own `node_modules` (`serverless-vpc-plugin`, `yn`, `aws-sdk`, the
  deployment-bucket and safeguards plugins). `customlib/` is gitignored: delete the folder and re-run the entrypoint to
  pick up a new library version.
- Configured only through environment variables (`.envs/config.env`; `DEPLOY_APP` from `.docker/docker-compose.yml`):
  `vpcPlugin.js` reads `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY`, `LIBCFNVPC_VPC_SERVICES`, `LIBCFNVPC_VPC_SUBNET_GROUPS`,
  `LIBCFNVPC_VPC_CREATE_DB_SUBNET`, `LIBCFNVPC_BASTION_KEY_PAIR_NAME`; the database resolvers read `LIBCFNVPC_DB_PORT`,
  `LIBCFNVPC_DB_ACCESS_VIA_PROXY`, `LIBCFNVPC_DB_IS_PUBLICLY_ACCESSIBLE`. Meanings: the library's README (cited from
  `README.md` → Glossary).
- Values chosen here and why:
  - `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY=false` — Studio uses `PublicInternetOnly`; a NAT gateway would be pure cost.
  - `LIBCFNVPC_DB_PORT=5432` — workaround: `database/proxy.yml` is always included and resolves
    `${env:LIBCFNVPC_DB_PORT}` without a default; setting it also enables `database/db.yml` (an unused
    `DatabaseSecurityGroup`) and `application/ec2.yml`. The proper fix belongs to the library repository.
  - `LIBCFNVPC_VPC_CREATE_DB_SUBNET` left at its default (`true`): with `false`, the plugin still publishes a
    `DBSubnets` parameter built from an empty list, which risks an empty SSM value (unverified — keep the default).
  - No bastion, no subnet groups, no VPC endpoints.
- Never edit files under `customlib/`: changes are lost on re-clone and diverge from the library. Propose them to the
  library repository.
