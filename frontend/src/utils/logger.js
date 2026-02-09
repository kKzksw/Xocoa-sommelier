/**
 * Conditional logger for XOCOA-Sommelier
 * Only logs debug/info in debug mode (DEBUG=true or NODE_ENV=development)
 * Warnings and errors always log
 */

const IS_DEBUG = process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development'

const logger = {
  debug: (...args) => IS_DEBUG && console.log(...args),
  info: (...args) => IS_DEBUG && console.log(...args),
  warn: (...args) => console.warn(...args),
  error: (...args) => console.error(...args)
}

module.exports = { logger, IS_DEBUG }
