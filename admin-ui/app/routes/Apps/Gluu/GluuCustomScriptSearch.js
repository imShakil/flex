import React from 'react'
import { Input, InputGroup, CustomInput, FormGroup } from 'Components'
import { useTranslation } from 'react-i18next'

function GluuCustomScriptSearch({
  handler,
  patternId,
  typeId,
  scriptType,
  pattern = '',
  options = []
}) {
  const { t } = useTranslation()
  return (
    <FormGroup row style={{ marginTop: '10px' }}>
      <InputGroup style={{ width: '210px' }}>
        <CustomInput
          type="select"
          name="type"
          data-testid={typeId}
          id={typeId}
          defaultValue={scriptType}
          onChange={handler}
          className="search-select"
        >
          {options.map((option) => {
            return <option key={option.value} value={option.value}>{option.name}</option>
          })}
        </CustomInput>
      </InputGroup>
      &nbsp;
      <Input
        style={{ width: '180px' }}
        id={patternId}
        type="text"
        data-testid={patternId}
        name="pattern"
        onChange={handler}
        defaultValue={pattern}
        placeholder={t('placeholders.search_pattern')}
      />
    </FormGroup>
  )
}

export default GluuCustomScriptSearch
