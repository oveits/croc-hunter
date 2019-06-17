#!/usr/bin/groovy

// load pipeline functions
// Requires pipeline-github-lib plugin to load library from github

@Library('github.com/oveits/jenkins-pipeline@feature/0009-refactor-into-separate-files-config-helm-kube')

def pipeline = [:]
pipeline.configuration = new com.voconit.pipeline.Configuration()
pipeline.docker = new com.voconit.pipeline.Docker()
pipeline.helm = new com.voconit.pipeline.Helm()
pipeline.kubectl = new com.voconit.pipeline.Kubectl()

def configuration = [:]
configuration = [
  app:[
    name:"croc-hunter",
    programmingLanguage:"golang",
    replicas:3,
    cpu:"10m",
    memory:"128Mi",
    test: true,
    hostname:"crochunter.vocon-it.com"
  ],
  k8s_secret:[
    name:"croc-hunter-secrets"
  ],
  container_repo:[
    host:"docker.io",
    master_acct:"oveits",
    alt_acct:"oveits",
    jenkins_creds_id:"oveits_docker_hub",
    repo:"crochunter",
    dockeremail:".",
    dockerfile:"./",
    image_scanning:false
  ],
  test_container_repo:[
    host:"docker.io",
    master_acct:"oveits",
    alt_acct:"oveits",
    jenkins_creds_id:"oveits_docker_hub",
    repo:"crochunter-tests",
    dockeremail:".",
    dockerfile:"./tests/",
    image_scanning:false
  ],
  pipeline:[
      enabled:true,
      debug:true,
      library:[
        branch:"dev"
      ]
  ]
]


podTemplate(label: 'jenkins-pipeline', 
  containers: [
    containerTemplate(
      name: 'jnlp', 
      image: 'jenkinsci/jnlp-slave:3.19-1-alpine', 
      args: '${computer.jnlpmac} ${computer.name}', 
      workingDir: '/home/jenkins', 
      resourceRequestCpu: '200m', 
      resourceLimitCpu: '300m', 
      resourceRequestMemory: '256Mi', 
      resourceLimitMemory: '512Mi'
    ),
    containerTemplate(
      name: 'docker', 
      image: 'docker:latest', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'golang', 
      image: 'golang:1.8.3', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'helm', 
      image: 'lachlanevenson/k8s-helm:v2.12.1', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'kubectl', 
      image: 'lachlanevenson/k8s-kubectl:v1.14.1', 
      command: 'cat', 
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'curl', 
      image: 'tutum/curl:trusty', 
      command: 'cat', 
      ttyEnabled: true
    )    
  ],
  volumes: [
    hostPathVolume(mountPath: '/var/run/docker.sock', hostPath: '/var/run/docker.sock'),
  ]
){

  node ('jenkins-pipeline') {
    properties([
      buildDiscarder(
        logRotator(artifactDaysToKeepStr: '', 
        artifactNumToKeepStr: '', 
        daysToKeepStr: '', 
        numToKeepStr: '30')), 
      disableConcurrentBuilds()])

    stage('Check out from SCM') {
      checkout scm
    }

    stage ('enrich configuration') {

      // DEFAULTS
      configuration.chart_dir               = "${pwd()}/charts/croc-hunter"
      configuration = pipeline.configuration.setDefaults(configuration)
      
      // prepare deployment variables
      // contains "croc-hunter", which is valid for this project only
      // TODO: change by variables or remove "croc-hunter" altogether
      configuration.testSeleniumHubUrl = "http://${configuration.seleniumRelease}-selenium-hub.${configuration.seleniumNamespace}.svc.cluster.local:4444/wd/hub"
      if(env.BRANCH_NAME ==~ /prod/) {
          configuration.ingressEnabled = true
          configuration.ingressHostname = configuration.app.hostname
          configuration.testIngressHostname = configuration.app.hostname
      } else {
          configuration.ingressEnabled = false
          configuration.ingressHostname = ""
          configuration.testIngressHostname = "${configuration.appRelease}-croc-hunter.${configuration.appNamespace}.svc.cluster.local"
      }
    }

    stage('preflight checks & init') {
      println "Test kubectl connectivity"
      container('kubectl') {
        pipeline.kubectl.getNodes()
      }
      println "Initializing helm"
      container('helm') {
        pipeline.helm.init()
      }
    }

    // TODO: move to pipeline:vars/configurationPrint.groovy
    //String call(Map configuration){
    String configurationPrintString = "Configuration:\n"
      for (s in configuration) {
        configurationPrintString += "${s.key.padRight(30)}:\t${s.value}\n"
      }
    // return configurationPrintString
    // }
    echo configurationPrintString


    // config vars:
    def     acct                 = configuration.acct
    String  chart_dir            = configuration.chart_dir
    boolean alwaysPerformTests   = configuration.alwaysPerformTests
    boolean debugPipeline        = configuration.debugPipeline
    boolean sharedSelenium       = configuration.sharedSelenium
    boolean skipRemoveTestPods   = configuration.skipRemoveTestPods
    boolean showHelmTestLogs     = configuration.showHelmTestLogs
    boolean debugHelmStatus      = configuration.debug.helmStatus
    Integer helmTestRetry        = configuration.helmTestRetry

    String  appRelease            = configuration.appRelease
    String  appNamespace          = configuration.appNamespace
    String  branchNameNormalized  = configuration.branchNameNormalized
    String  seleniumRelease       = configuration.seleniumRelease
    String  seleniumNamespace     = configuration.seleniumNamespace
    boolean skipRemoveApp         = configuration.skipRemoveApp
    String  commitTag             = configuration.commitTag
    def     image_tags_list       = configuration.image_tags_list

    // deployment variables:
    boolean ingressEnabled        = configuration.ingressEnabled
    String  ingressHostname       = configuration.ingressHostname
    String  testIngressHostname   = configuration.testIngressHostname
    String  testSeleniumHubUrl    = configuration.testSeleniumHubUrl

    // working vars:
    def     helmStatus
    String  testLog


    stage ('build') {
      container(configuration.app.programmingLanguage) {
        sh configuration.buildCommand
      }
    }

    stage ('unit test')  {
      container(configuration.app.programmingLanguage) {
        sh configuration.unitTestCommand
      }
    }

    // TODO: replace by pipeline.helm.purgeNonDeployed() ??
    stage('clean old versions, if not DEPLOYED') {
      container('helm') {
        helmStatus = pipeline.helm.status(
          name    : appRelease
        )
        if(helmStatus && helmStatus.info && helmStatus.info.status && helmStatus.info.status.code != 1) {
          sh """
            helm delete --purge ${appRelease}
          """
        }
      }
    }

    stage ('deployment dry-run') {

      container('helm') {

        // run helm chart linter
        pipeline.helm.lint(chart_dir)

        // run dry-run helm chart installation
        pipeline.helm.deploy (
          dry_run       : true,
          name          : appRelease,
          namespace     : appNamespace,
          chart_dir     : chart_dir,
          set_string    : [
            "commit.sha": commitTag,
          ],
          set           : [
            "imageTag": image_tags_list.get(0),
            "replicas": configuration.app.replicas,
            "cpu": configuration.app.cpu,
            "memory": configuration.app.memory,
            "ingress.enabled": ingressEnabled,
            "ingress.hostname": ingressHostname,
            "imagePullSecrets.name": configuration.k8s_secret.name,
            "imagePullSecrets.repository": configuration.container_repo.host,
            "imagePullSecrets.username": env.USERNAME,
            "imagePullSecrets.password": env.PASSWORD,
            // "imagePullSecrets.email": "ServicePrincipal@AzureRM",
            "test.seleniumHubUrl": testSeleniumHubUrl,
            "test.ingressHostname": testIngressHostname,
            "test.imageTag": image_tags_list.get(0),
            "test.releaseName": appRelease,   
          ]
        )
      }
    }

    stage ('publish docker image of app') {

      container('docker') {

        // build and publish container
        pipeline.docker.buildAndPublish(
            dockerfile: configuration.container_repo.dockerfile,
            host      : configuration.container_repo.host,
            acct      : acct,
            repo      : configuration.container_repo.repo,
            tags      : image_tags_list,
            auth_id   : configuration.container_repo.jenkins_creds_id,
            image_scanning: configuration.container_repo.image_scanning
        )
      }

    }

    if (alwaysPerformTests || env.BRANCH_NAME =~ "PR-*" || env.BRANCH_NAME == "develop" || env.BRANCH_NAME ==~ /prod/) {

      stage('Deploy Selenium') {
        //
        // Deploy Selenium using Helm chart
        // will not wait for Seöenium to be up and running to save time (is done in a later stage)
        //
        // TODO: in the moment, only a single Chrome Selenium Node is started (hard-coded). Please make this dynamic
        //       if so, this also needs to be changed in the stage "Selenium complete?"
        //
        container('helm') {
          // Delete and purge selenium, if present
          if ( !sharedSelenium ) {
            echo "delete and purge selenium, if present"
            sh """
              helm list -a --output yaml | grep 'Name: ${seleniumRelease}\$' \
                && helm delete --purge ${seleniumRelease} || true
            """
          }

          // Deploy Selenium:
          sh """
            # upgrade selenium revision. Install, if not present:
            helm upgrade --install ${seleniumRelease} stable/selenium \
              --namespace ${seleniumNamespace} \
              --set chromeDebug.enabled=true \
              --force
          """
        }

      }
   
      if (debugHelmStatus) {
        stage('DEBUG: get helm status BEFORE Clean App') {
          container('helm') {
            helmStatus = pipeline.helm.status(
              name    : appRelease
            )
          }        
          container('kubectl') {
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      if (env.BRANCH_NAME != "prod") {
        stage('Clean App'){
          // Clean App using Helm
          container('helm') {

            // purge old versions of ${appRelease}, if present (will find and purge deleted versions as well)
            sh """
              # purge deleted versions of ${appRelease}, if present
              helm list -a --output yaml | grep 'Name: ${appRelease}\$' \
                && helm delete --purge ${appRelease} || true
            """
            // TODO: purge only DELETED versions
            // if jq is installed, we could use something like follows to find all FAILED or DELETED releases with Name "pr-15":
            //    helm ls --output json | jq '.Releases | map( select( ((.Status=="FAILED") or (.Status=="DELETED")) and (.Name=="pr-15") ) )'
            // or with regular expressions and a pipe in a next map(select(...)) instead of an "and" operator:
            //    helm ls --output json | jq '.Releases | map( select(.Status|test("^FAILED$|^DELETED$") )) | map( select(.Name|test("^pr-15$") ))'
            // another possibility is to define an object helmList
            //    helmList = sh script: "helm list -a --output json"
          }
        }

        if (debugHelmStatus) {
          stage('DEBUG: get helm status AFTER Clean App'){
            container('helm') {
              helmStatus = pipeline.helm.status(
                name    : appRelease
              )
            }
            container('kubectl') {
              sh "kubectl -n ${appNamespace} get all || true"
            }
          }
        }
      }

      stage ('Deploy App') {
        // Deploy using Helm chart
        //
        container('helm') {

          withCredentials([[$class          : 'UsernamePasswordMultiBinding', credentialsId: configuration.container_repo.jenkins_creds_id,
                        usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {

            pipeline.helm.deploy(
                dry_run       : false,
                name          : appRelease,
                namespace     : appNamespace,
                chart_dir     : chart_dir,
                set_string    : [
                  "commit.sha": commitTag,
                ],
                set           : [
                  "imageTag": image_tags_list.get(0),
                  "replicas": configuration.app.replicas,
                  "cpu": configuration.app.cpu,
                  "memory": configuration.app.memory,
                  "ingress.enabled": ingressEnabled,
                  "ingress.hostname": ingressHostname,
                  "imagePullSecrets.name": configuration.k8s_secret.name,
                  "imagePullSecrets.repository": configuration.container_repo.host,
                  "imagePullSecrets.username": env.USERNAME,
                  "imagePullSecrets.password": env.PASSWORD,
                  // "imagePullSecrets.email": "ServicePrincipal@AzureRM",
                  "test.seleniumHubUrl": testSeleniumHubUrl,
                  "test.ingressHostname": testIngressHostname,
                  "test.imageTag": image_tags_list.get(0),
                  "test.releaseName": appRelease,
                ]
              )
          }
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status AFTER Deploy App'){
          container('helm') {
            helmStatus = pipeline.helm.status(
              name    : appRelease
            )
          }        
          container('kubectl') {
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      stage ('Selenium complete?') {
        // wait for Selenium deployments, if needed
        container('kubectl') {
          sh "kubectl rollout status --watch deployment/${seleniumRelease}-selenium-hub -n ${seleniumNamespace} --timeout=5m"
          sh "kubectl rollout status --watch deployment/${seleniumRelease}-selenium-chrome-debug -n ${seleniumNamespace} --timeout=5m"
        }

        // wait for the chrome node to be registered at the hub
        container('curl') {
          sh "until curl -v -s -D - http://${seleniumRelease}-selenium-hub.${seleniumNamespace}.svc.cluster.local:4444/grid/console | grep -m 1 'browserName=chrome'; do echo 'still waiting for a chrome node to register with the Selenium hub...' && sleep 5 ; done"
        }
      }

      stage ('Create and Push Selenium Test Docker Image') {
        container('docker') {
          pipeline.docker.buildAndPublish(
              dockerfile: configuration.test_container_repo.dockerfile,
              host      : configuration.test_container_repo.host,
              acct      : acct,
              repo      : configuration.test_container_repo.repo,
              tags      : image_tags_list,
              auth_id   : configuration.test_container_repo.jenkins_creds_id,
              image_scanning: configuration.test_container_repo.image_scanning
          )
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status BEFORE delete completed PODs if present') {
          container('helm') {
            helmStatus = pipeline.helm.status(
              name    : appRelease
            )
          }        
          container('kubectl') {
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      stage('delete completed PODs if present') {
        container('kubectl') {
          sh """
          PODS=\$(kubectl -n ${appNamespace} get pods | grep 'Completed\\|Error' | awk '{print \$1}')
          if [ "\$PODS" != "" ]; then
            echo \$PODS | xargs -n 1 kubectl -n ${appNamespace} delete pod
          else
            echo "no completed PODs found; continuing"
          fi
          """
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status AFTER delete old UI test containers (new way)') {
          container('helm') {
            helmStatus = pipeline.helm.status(
              name    : appRelease
            )
          }        
          container('kubectl') {
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }
 
      stage ('UI Tests') {
        // depends on: stage('delete completed PODs if present')
        
        //  Run helm tests

        if (configuration.app.test) {

          // run tests
          container('helm') {
            testLog = sh script: "helm test ${appRelease} 2>&1 || echo 'SUCCESS=false'", returnStdout: true
          }

          echo ""
          // retrying the helm test:
          while(helmTestRetry != null && helmTestRetry > 0 && testLog ==~ /(?sm).*SUCCESS=false.*/) {
            helmTestRetry = helmTestRetry - 1
            echo "helm test has failed. Re-trying..."

            echo "cleaning:"
            container('kubectl'){
              sh "kubectl -n ${appNamespace} get pods | grep 'Completed\\|Error' | awk '{print \$1}' | xargs -n 1 kubectl -n ${appNamespace} delete pod || true"
            }

            echo "testing:"
            container('helm') {
              testLog = sh script: "helm test ${appRelease} 2>&1 || echo 'SUCCESS=false'", returnStdout: true
            }
          }      

          // show logs of test pods:
          if(showHelmTestLogs) {
            // read helm status
            container('helm') {
              helmStatus = pipeline.helm.status(
                name    : appRelease
              )
            } 

            // show logs:
            container('kubectl') {
              if(helmStatus.info.status.last_test_suite_run != null) {
                helmStatus.info.status.last_test_suite_run.results.each { result ->
                  sh "kubectl -n ${helmStatus.namespace} logs ${result.name} || true"
                }
              }
            }
          }

          // delete test pods
          if(!skipRemoveTestPods) {
            // read helm status
            container('helm') {
              helmStatus = pipeline.helm.status(
                name    : appRelease
              )
            } 

            // delete test pods
            container('kubectl') {
              if(helmStatus.info.status.last_test_suite_run != null) {
                  helmStatus.info.status.last_test_suite_run.results.each { result ->
                  sh "kubectl -n ${helmStatus.namespace} delete pod ${result.name} || true"
                }
              }
            }
          }

          // fail, if all test runs have failed
          if(testLog ==~ /(?sm).*SUCCESS=false.*/) {
            echo "ERROR: test has failed. Showing log and exiting"
            echo "testLog = ${testLog}"
            sh "exit 1"
          }
        }
      }

      if (skipRemoveApp == false) {
        stage ('Remove App') {
          container('helm') {
            // delete test deployment
            pipeline.helm.delete(
                name       : appRelease
            )
          }
        }
      }

      if ( !sharedSelenium ) {
        stage('Remove Selenium') {
          // Delete Helm revision
          container('helm') {
            // init
            println "initialzing helm client"
            sh "helm init"
            println "checking client/server version"
            sh "helm version"
            
            println "deleting and purging selenium, if present"
            sh """
              helm list -a --output yaml | grep 'Name: ${seleniumRelease}\$' \
                && helm delete --purge ${seleniumRelease}
            """
          }
        }
      }
    }
  }
}
