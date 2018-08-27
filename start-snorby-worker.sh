#!/bin/sh -x

echo "Starting Snorby worker (Snorby::Worker.start)"
cd "/var/www/snorby" && RAILS_ENV=production bundle exec rails runner 'Snorby::Worker.start; Snorby::Jobs::SensorCacheJob.new(false).perform; Snorby::Jobs::DailyCacheJob.new(false).perform'
