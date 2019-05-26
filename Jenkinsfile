#!/usr/bin/groovy

// load pipeline functions
// Requires pipeline-github-lib plugin to load library from github

@Library('github.com/oveits/jenkins-pipeline@develop')

def configuration = [:]

// Example:
// configuration = [
//   sharedSelenium:true,
//   skipRemoveApp:true, 
//   skipRemoveTestPods:false,
//   showHelmTestLogs:true,
//   debug:[
//     helmStatus:false
//   ]
// ]

// DEFAULTS
configuration.alwaysPerformTests      = configuration.alwaysPerformTests != null     ?    configuration.alwaysPerformTests       : (env.getProperty('ALWAYS_PERFORM_TESTS')         != null ? (env.getProperty('ALWAYS_PERFORM_TESTS')         == "true" ? true : false) : false)
configuration.debugPipeline           = configuration.debugPipeline != null          ?    configuration.debugPipeline            : (env.getProperty('DEBUG_PIPELINE')               != null ? (env.getProperty('DEBUG_PIPELINE')               == "true" ? true : false) : false)
configuration.sharedSelenium          = configuration.sharedSelenium != null         ?    configuration.sharedSelenium           : (env.getProperty('SHARED_SELENIUM')              != null ? (env.getProperty('SHARED_SELENIUM')              == "true" ? true : false) : false)
// configuration.seleniumRelease:     will be set further below
// configuration.seleniumNamespace:   will be set further below
configuration.skipRemoveAppIfNotProd  = configuration.skipRemoveAppIfNotProd != null  ?    configuration.skipRemoveAppIfNotProd  : (env.getProperty('SKIP_REMOVE_APP_IF_NOT_PROD')  != null ? (env.getProperty('SKIP_REMOVE_APP_IF_NOT_PROD')  == "true" ? true : false) : false)
configuration.skipRemoveTestPods      = configuration.skipRemoveTestPods != null      ?    configuration.skipRemoveTestPods      : (env.getProperty('SKIP_REMOVE_TEST_PODS')        != null ? (env.getProperty('SKIP_REMOVE_TEST_PODS')        == "true" ? true : false) : false)
configuration.showHelmTestLogs        = configuration.showHelmTestLogs != null        ?    configuration.showHelmTestLogs        : (env.getProperty('SHOW_HELM_TEST_LOGS')          != null ? (env.getProperty('SHOW_HELM_TEST_LOGS')          == "true" ? true : false) : true)
configuration.debug                   = configuration.debug != null                   ?    configuration.debug                   : [:]
configuration.debug.helmStatus        = configuration.debug.helmStatus != null        ?    configuration.debug.helmStatus        : (env.getProperty('DEBUG_HELM_STATUS')            != null ? (env.getProperty('DEBUG_HELM_STATUS')            == "true" ? true : false) : false)
configuration.helmTestRetry           = configuration.helmTestRetry != null           ?    configuration.helmTestRetry           : (env.getProperty('HELM_TEST_RETRY')              != null ? env.getProperty('HELM_TEST_RETRY').toInteger()                        : 0)

// TODO: move to pipeline:vars/configurationPrint.groovy
//String call(Map configuration){
String configurationPrintString = "Configuration:\n"
  for (s in configuration) {
    configurationPrintString += "${s.key.padRight(30)}:\t${s.value}\n"
  }
// return configurationPrintString
// }
echo configurationPrintString

// INIT
def pipeline = new io.estrado.Pipeline()
boolean alwaysPerformTests   = configuration.alwaysPerformTests
boolean debugPipeline        = configuration.debugPipeline
boolean sharedSelenium       = configuration.sharedSelenium
// boolean skipRemoveApp        = configuration.skipRemoveAppIfNotProd
boolean skipRemoveTestPods   = configuration.skipRemoveTestPods
boolean showHelmTestLogs     = configuration.showHelmTestLogs
boolean debugHelmStatus      = configuration.debug.helmStatus
Integer helmTestRetry        = configuration.helmTestRetry

String  appRelease            = "to-be-changed"
String  appNamespace          = "to-be-changed"
def helmStatus
String  testLog
String  branchNameNormalized  = "to-be-changed"
String  seleniumRelease       = "to-be-changed"
String  seleniumNamespace     = "to-be-changed"
boolean skipRemoveApp         = null


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

    def pwd = pwd()
    def chart_dir = "${pwd}/charts/croc-hunter"
    // following vars are defined in stage 'Prepare and SCM' and are used in subsequent stages:
    def inputFile
    def config
    def acct
    def image_tags_map
    def image_tags_list

    stage('Prepare and SCM') {

      checkout scm

      env.GIT_SHA = sh script: "echo \${GIT_REVISION:0:7}", returnStdout: true

      // Create normalized branch name
      // - replaces '/' by '-' 
      // - shortens branch name, if needed. In that case, add a 6 Byte hash
      branchNameNormalized = env.BRANCH_NAME.toLowerCase().replaceAll('/','-')
      if (branchNameNormalized.length() > 30) {
        String digest = sh script: "echo ${env.BRANCH_NAME} | md5sum | cut -c1-6 | tr -d '\\n' | tr -d '\\r'", returnStdout: true
        branchNameNormalized = branchNameNormalized.take(24) + '-' + digest
        if (debugPipeline) {
          echo "digest = ${digest}"
        }
      }
      echo "branchNameNormalized = ${branchNameNormalized}"
      configuration.branchNameNormalized = branchNameNormalized

      // read in required jenkins workflow config values
      inputFile = readFile('Jenkinsfile.json')
      config = new groovy.json.JsonSlurperClassic().parseText(inputFile)
      println "pipeline config ==> ${config}"

      // set appRelease:
      appRelease    = env.BRANCH_NAME == "prod" ? config.app.name : branchNameNormalized
      appNamespace  = env.BRANCH_NAME == "prod" ? config.app.name : branchNameNormalized
      skipRemoveApp = env.BRANCH_NAME == "prod" ? true            : configuration.skipRemoveAppIfNotProd

      // Set Selenium configuration
      configuration.seleniumRelease       = configuration.sharedSelenium == true      ?    'selenium'   : (appRelease + '-selenium')
      configuration.seleniumNamespace     = configuration.sharedSelenium == true      ?    'selenium'   : appNamespace
      seleniumRelease   = configuration.seleniumRelease
      seleniumNamespace = configuration.seleniumNamespace


      // continue only if pipeline enabled
      if (!config.pipeline.enabled) {
          println "pipeline disabled"
          return
      }

      // set additional git envvars for image tagging
      pipeline.gitEnvVars()

      // If pipeline debugging enabled
      if (config.pipeline.debug) {
        println "DEBUG ENABLED"
        sh "env | sort"

        println "Runing kubectl/helm tests"
        container('kubectl') {
          pipeline.kubectlTest()
        }
        container('helm') {
          pipeline.helmConfig()
        }
      }

      acct = pipeline.getContainerRepoAcct(config)

      // tag image with version, and branch-commit_id
      image_tags_map = pipeline.getContainerTags(config)

      // compile tag list
      image_tags_list = pipeline.getMapValues(image_tags_map)

      echo "image_tags_list = ${image_tags_list}"

      // initialize helm container
      container('helm') {
          // init
          println "initialzing helm client"
          sh "helm init"
          println "checking client/server version"
          sh "helm version"
      }
    }

    stage ('compile and test') {

      container('golang') {
        sh "go test -v -race ./..."
        sh "make bootstrap build"
      }
    }

    stage ('test deployment') {

      container('helm') {

        // run helm chart linter
        pipeline.helmLint(chart_dir)

        // run dry-run helm chart installation
        pipeline.helmDeploy(
          dry_run       : true,
          name          : config.app.name,
          namespace     : config.app.name,
          chart_dir     : chart_dir,
          set           : [
            "imageTag": image_tags_list.get(0),
            "replicas": config.app.replicas,
            "cpu": config.app.cpu,
            "memory": config.app.memory,
            "ingress.hostname": config.app.hostname,
            "imagePullSecrets.name": config.k8s_secret.name,
            "imagePullSecrets.repository": config.container_repo.host,
            "imagePullSecrets.username": env.USERNAME,
            "imagePullSecrets.password": env.PASSWORD,
            "imagePullSecrets.email": "ServicePrincipal@AzureRM",
          ]
        )

      }
    }

    stage ('publish docker image') {

      container('docker') {

        // build and publish container
        pipeline.containerBuildPub(
            dockerfile: config.container_repo.dockerfile,
            host      : config.container_repo.host,
            acct      : acct,
            repo      : config.container_repo.repo,
            tags      : image_tags_list,
            auth_id   : config.container_repo.jenkins_creds_id,
            image_scanning: config.container_repo.image_scanning
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
          // delete and purge selenium, if present
          if ( !sharedSelenium ) {
            echo "delete and purge selenium, if present"
            sh """
              helm list -a --output yaml | grep 'Name: ${seleniumRelease}\$' \
                && helm delete --purge ${seleniumRelease} || true
            """
          }

          // always:
          sh """
            # upgrade selenium revision. Install, if not present:
            helm upgrade --install ${seleniumRelease} stable/selenium \
              --namespace ${seleniumNamespace} \
              --set chromeDebug.enabled=true \
              --force
          """
        }

      }
   
      // DEBUG
      if (debugHelmStatus) {
        stage('DEBUG: get helm status BEFORE Clean App'){
          container('helm') {
            helmStatus = pipeline.helmStatus(
              name    : appRelease
            )
          }
          container('kubectl'){
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      stage('Clean App'){
        // Clean App using Helm
        container('helm') {

          // purge deleted versions of ${appRelease}, if present
          sh """
            # purge deleted versions of ${appRelease}, if present
            helm list -a --output yaml | grep 'Name: ${appRelease}\$' \
              && helm delete --purge ${appRelease} || true
          """
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status AFTER Clean App'){
          container('helm') {
            helmStatus = pipeline.helmStatus(
              name    : appRelease
            )
          }
          container('kubectl') {
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      stage ('Deploy App') {
        // Deploy using Helm chart
        //
        // TODO: better use a single pipeline.helmDeploy. For that, change variables before running the command.
        //       e.g. 
        container('helm') {

          // purge deleted versions of ${appRelease}, if present
          sh """
            # purge deleted versions of ${appRelease}, if present
            helm list -a --output yaml | grep 'Name: ${appRelease}\$' \
              && helm delete --purge ${appRelease} || true
          """

                    // Create secret from Jenkins credentials manager
          withCredentials([[$class          : 'UsernamePasswordMultiBinding', credentialsId: config.container_repo.jenkins_creds_id,
                        usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            boolean ingressEnabled
            String  ingressHostname
            String  testIngressHostname
            String  testSeleniumHubUrl = "http://${seleniumRelease}-selenium-hub.${seleniumNamespace}.svc.cluster.local:4444/wd/hub"

            if(env.BRANCH_NAME ==~ /prod/) {
              ingressEnabled = true
              ingressHostname = config.app.hostname
              testIngressHostname = config.app.hostname
            } else {
              ingressEnabled = false
              ingressHostname = ""
              testIngressHostname = "${appRelease}-croc-hunter.${appNamespace}.svc.cluster.local"
            }

            pipeline.helmDeploy(
                dry_run       : false,
                name          : appRelease,
                namespace     : appNamespace,
                chart_dir     : chart_dir,
                set           : [
                  "imageTag": image_tags_list.get(0),
                  "replicas": config.app.replicas,
                  "cpu": config.app.cpu,
                  "memory": config.app.memory,
                  "ingress.enabled": ingressEnabled,
                  "ingress.hostname": ingressHostname,
                  // "imagePullSecrets.name": config.k8s_secret.name,
                  "imagePullSecrets.repository": config.container_repo.host,
                  // "imagePullSecrets.username": env.USERNAME,
                  // "imagePullSecrets.password": env.PASSWORD,
                  // "imagePullSecrets.email": "ServicePrincipal@AzureRM",
                  "test.seleniumHubUrl": testSeleniumHubUrl,
                  "test.ingressHostname": testIngressHostname,
                  "test.imageTag": image_tags_list.get(0),
                  "test.releaseName": appRelease,
                  "commit.sha": env.GIT_SHA,
                ]
              )
          }
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status AFTER Deploy App'){
          container('helm') {
            helmStatus = pipeline.helmStatus(
              name    : appRelease
            )
          }        
          container('kubectl'){
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }

      stage ('PR: Selenium complete?') {
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
          pipeline.containerBuildPub(
              dockerfile: config.test_container_repo.dockerfile,
              host      : config.test_container_repo.host,
              acct      : acct,
              repo      : config.test_container_repo.repo,
              tags      : image_tags_list,
              auth_id   : config.test_container_repo.jenkins_creds_id,
              image_scanning: config.test_container_repo.image_scanning
          )
        }
      }

      stage('get helm status'){
        container('helm') {
          // get helm status
          def helmStatusText = sh script: "helm status ${appRelease} -o json", returnStdout: true
          echo helmStatusText
          helmStatus = readJSON text: helmStatusText

          // echo helmStatus
        }

        // print all resources in namespace:
        container('kubectl'){
          sh "kubectl -n ${helmStatus.namespace} get all"
        }
      }

      stage('delete completed PODs if present') {
        container('kubectl'){
          sh "kubectl -n ${appNamespace} get pods | grep 'Completed\\|Error' | awk '{print \$1}' | xargs -n 1 kubectl -n ${appNamespace} delete pod || true"
        }
      }

      if (debugHelmStatus) {
        stage('DEBUG: get helm status AFTER delete old UI test containers (new way)') {
          container('helm') {
            helmStatus = pipeline.helmStatus(
              name    : appRelease
            )
          }        
          container('kubectl'){
            sh "kubectl -n ${appNamespace} get all || true"
          }
        }
      }
 
      stage ('UI Tests') {
        // depends on: stage('delete old UI test containers, if needed')
        
        //  Run helm tests

        if (config.app.test) {

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

          // read helm status
          container('helm') {
            helmStatus = pipeline.helmStatus(
              name    : appRelease
            )
          }          

          // show logs of test pods:
          if(showHelmTestLogs) {
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
        stage ('PR: Remove App') {
          container('helm') {
            // delete test deployment
            pipeline.helmDelete(
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
